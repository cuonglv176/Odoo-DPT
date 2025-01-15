# -*- coding: utf-8 -*-
##############################################################################
#
#    EQP Solutions
#
#    Copyright (C) 2024-TODAY EQP Solutions (<https://www.eqpsolutions.com>)
#    Author: EQP Solutions (<info@eqpsolutions.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import odoo
import glob
import json
import shutil
import logging
import tempfile
import subprocess

from odoo import models, fields, _
from odoo.service import db
from odoo.exceptions import ValidationError
from datetime import datetime, timezone

from odoo.tools import find_pg_tool, exec_pg_environ

_logger = logging.getLogger(__name__)


# Overwriting the "db functions" to prevent that list_db=False will block the process


def dump_db_manifest(cr):
    pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
    cr.execute(
        "SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'"
    )
    modules = dict(cr.fetchall())
    manifest = {
        "odoo_dump": "1",
        "db_name": cr.dbname,
        "version": odoo.release.version,
        "version_info": odoo.release.version_info,
        "major_version": odoo.release.major_version,
        "pg_version": pg_version,
        "modules": modules,
    }
    return manifest


def dump_db(db_name, stream, backup_format="zip"):
    """Dump database `db` into file-like object `stream` if stream is None
    return a file object with the dump"""

    _logger.info("DUMP DB: %s format %s", db_name, backup_format)

    cmd = [find_pg_tool("pg_dump"), "--no-owner", db_name]
    env = exec_pg_environ()

    if backup_format == "zip":
        with tempfile.TemporaryDirectory() as dump_dir:
            filestore = odoo.tools.config.filestore(db_name)
            if os.path.exists(filestore):
                shutil.copytree(filestore, os.path.join(dump_dir, "filestore"))
            with open(os.path.join(dump_dir, "manifest.json"), "w") as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(dump_db_manifest(cr), fh, indent=4)
            cmd.insert(-1, "--file=" + os.path.join(dump_dir, "dump.sql"))
            subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                check=True,
            )
            if stream:
                odoo.tools.osutil.zip_dir(
                    dump_dir,
                    stream,
                    include_dir=False,
                    fnct_sort=lambda file_name: file_name != "dump.sql",
                )
            else:
                t = tempfile.TemporaryFile()
                odoo.tools.osutil.zip_dir(
                    dump_dir,
                    t,
                    include_dir=False,
                    fnct_sort=lambda file_name: file_name != "dump.sql",
                )
                t.seek(0)
                return t
    else:
        cmd.insert(-1, "--format=c")
        stdout = subprocess.Popen(
            cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE
        ).stdout
        if stream:
            shutil.copyfileobj(stdout, stream)
        else:
            return stdout


class BackupRecord(models.Model):
    """Model to manage EQP Automatic Backup Records."""

    _name = "backup.record"
    _description = "EQP Automatic Backup Records"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    active = fields.Boolean(
        default=True,
        tracking=True,
        string="Active",
        copy=False,
        help="Set active to false to hide the record without removing it.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible user",
        index=True,
        copy=False,
        required=True,
        ondelete="cascade",
        default=lambda self: self.env.user,
        tracking=True,
        help="Assign a responsible user for this Backup Record.",
    )

    name = fields.Char(string="Name", required=True, tracking=True, help="Record Name")
    description = fields.Text(
        string="Description", copy=False, help="Add a brief description of the record"
    )

    db_name = fields.Char(
        string="Database Name", required=True, tracking=True, help="Data Base name"
    )
    db_names = fields.Text(string="Available Databases", copy=False, readonly=True)
    frequency = fields.Selection(
        [
            ("years", "Yearly"),
            ("months", "Monthly"),
            ("weeks", "Weekly"),
            ("days", "Daily"),
            ("hours", "Hourly"),
        ],
        string="Backup Frequency",
        required=True,
        tracking=True,
        help="Select the frequency at which you would like your backups to be generated.",
    )
    backup_lifespan_qty = fields.Integer(
        string="Backup Lifespan qty",
        required=True,
        tracking=True,
        default=-1,
        help="When the number of backups exceeds this limit, the system will "
        "automatically delete the older backups, ensuring that only the "
        "specified number of backups are retained.\n"
        "To DISABLE this functionality put '-1'.",
    )
    success_mail_send = fields.Boolean(
        string="Email when Success",
        copy=False,
        tracking=True,
        help="Send an email when the backup process is executed Successfully.",
    )
    failure_mail_send = fields.Boolean(
        string="Email when Failure",
        copy=False,
        tracking=True,
        help="Send an email when the backup process present a Failure .",
    )
    success_mail_policy = fields.Boolean(
        related="company_id.eqp_backup_enable_success_email"
    )
    failure_mail_policy = fields.Boolean(
        related="company_id.eqp_backup_enable_failure_email"
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("paused", "Paused"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        tracking=True,
        copy=False,
        help="Backup Record Status (If the status is 'Paused,' it indicates that the server is "
        "in a state other than 'confirmed.)",
    )
    server_id = fields.Many2one(
        "backup.server",
        string="Server",
        required=True,
        index=True,
        tracking=True,
        ondelete="restrict",
        help="Select a Backup server (Only Confirmed Servers can be used).",
    )
    cron_id = fields.Many2one(
        "ir.cron",
        string="Scheduled Action",
        readonly=True,
        tracking=True,
        ondelete="restrict",
        copy=False,
        help="Scheduled cron which ensures the automatic execution of backups at "
        "specific times.",
    )

    last_execution_result = fields.Text(
        string="Last Execution Result",
        readonly=True,
        help="Access the details of the most recent execution here.",
    )

    _sql_constraints = [
        ("name_unique", "unique(name, company_id)", "A unique name per company."),
        (
            "unique_cron_id",
            "UNIQUE(cron_id)",
            "One Cron should only have one BackUp record.",
        ),
        (
            "check_backup_lifespan_qty",
            "CHECK(backup_lifespan_qty = -1 OR backup_lifespan_qty > 1)",
            "The Backup span qty must be either -1 or greater than 1",
        ),
    ]

    def update_cron_state(self, state):
        """Update the state of the associated cron job.

        Args:
            state (bool): New state for the cron job (active/inactive).
        """
        for record in self:
            if record.cron_id:
                record.cron_id.write({"active": state})

    def write(self, vals):
        """Override write method to handle state updates.

        Args:
            vals (dict): Values to be written.

        Returns:
            dict: Written values.
        """
        if "active" in vals:
            if vals["active"] is True:
                vals["state"] = "draft"
            else:
                vals["state"] = "archived"
                self.update_cron_state(False)
        return super(BackupRecord, self).write(vals)

    def copy(self, default=None):
        """Create a copy of the backup record.

        Args:
            default (dict): Default values for the new record.

        Returns:
            models.Model: New backup record.
        """
        self.ensure_one()
        chosen_name = default.get("name") if default else ""
        new_name = chosen_name or _("%s (copy)", self.name)
        default = dict(default or {}, name=new_name)
        return super(BackupRecord, self).copy(default)

    def check_valid_state(self, just_server=False):
        """Check if the backup record is in a valid state for certain operations.

        Args:
            just_server (bool): If True, only check the state of the associated server.

        Raises:
            ValidationError: If the state is not valid.
        """
        for record in self:
            if not just_server and record.state != "confirmed":
                raise ValidationError(
                    'This method can only be executed on a Backup record in the "confirmed" state.'
                )
            if record.server_id.state != "confirmed":
                raise ValidationError(
                    'This method can only be executed with a Backup Server in the "confirmed" state.'
                )

    def revert_state(self):
        """Revert the state of the backup record to 'draft'.

        If the record is in the 'confirmed' state, it will be reverted to 'draft',
         and the associated cron job state will be updated if applicable.
        """
        for record in self:
            if record.cron_id:
                self.update_cron_state(False)
            if record.state == "confirmed":
                record.write({"state": "draft", "db_names": ""})

    def validate_db(self):
        """Validate database credentials and confirm backup record.

        Returns:
            dict: Action to display notification with validation result.
        """
        self.ensure_one()
        dbs = db.list_dbs(force=True)

        # Set a Success values by default.
        result_type = "success"
        result_msg = "Database validation executed Successfully."

        db_name = self.db_name
        # Validates if the database exists
        if db_name not in dbs:
            # Set a warning notification values by default (Display just on a strange case).
            result_type = "warning"
            result_msg = f'The specified Database Name "{db_name}" does not exist. Please verify and try again.'

        if result_type == "success" and self.env.context.get("confirm", False):

            # Validate confirmed state
            self.check_valid_state(True)
            # Create/update Cron
            vals = {"state": "confirmed"}

            # Define the Cron values
            model_id = self.env["ir.model"]._get_id("backup.record")
            cron_values = {
                "active": True,
                "name": f"{self.name} - Cron",
                "model_id": model_id,
                "state": "code",
                "code": f"model._scheduled_backup_process(record_id={self.id})",
                "numbercall": -1,
                "doall": False,
            }

            if self.cron_id:
                # Re-Write Existing Cron
                self.cron_id.write(cron_values)
            else:
                # Default interval_number and interval_type on the cron then the user can modify it if required.
                cron_values["interval_number"] = 1 if self.frequency != "years" else 12
                cron_values["interval_type"] = (
                    self.frequency if self.frequency != "years" else "months"
                )
                # Create new Cron
                cron_job = self.env["ir.cron"].create(cron_values)
                # Reference the cron with the Backup record
                vals["cron_id"] = cron_job and cron_job.id

            # Update State if the confirmation flag is true
            self.write(vals)

        # Display the test result
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "context": dict(self._context, active_ids=self.ids),
            "target": "new",
            "params": {
                "message": _(result_msg),
                "type": result_type,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def show_databases(self):
        """Update the 'db_names' field with the available databases."""
        dbs = db.list_dbs(force=True)
        dbs_txt = "\n".join(name for name in dbs)
        self.write({"db_names": dbs_txt})

    def notify_result(self, result_type):
        """Notify the result of the backup process.

        Args:
            result_type (str): Type of result (success/danger).
        """
        for record in self:
            template = None

            if (
                result_type == "success"
                and self.success_mail_send
                and self.success_mail_policy
            ):
                template = self.env.ref(
                    "eqp_backup.email_template_data_automatic_backup_success"
                )
            elif (
                result_type == "danger"
                and self.failure_mail_send
                and self.failure_mail_policy
            ):
                template = self.env.ref(
                    "eqp_backup.email_template_data_automatic_backup_failed"
                )
            if template:
                template.send_mail(record.id, force_send=True)

    def _scheduled_backup_process(self, record_id):
        """Perform the scheduled backup process.

        Args:
            record_id (int): ID of the backup record.

        Returns:
            bool: True if the process was successful, False otherwise.
        """
        # Instantiate both record and server
        record = self.browse(record_id)
        server = record.server_id

        # Validate confirmed state
        record.check_valid_state()

        # Set the backup file unique name
        db_name = record.db_name
        extension = "zip"

        # Get file path details
        destination_path, file_name = server.get_file_path_details(db_name, extension)
        file_path = destination_path + file_name

        backup_type = server.backup_type

        # Local backup
        if backup_type == "local":
            try:
                # Check if the file path exists
                if not os.path.isdir(destination_path):
                    # Try to create it if it does not exist
                    os.makedirs(destination_path)
                # Open with write permissions the file on the file path
                file = open(file_path, "wb")
                # Generate backup using the dump_db function
                dump_db(db_name, file, extension)
                # Closing the file
                file.close()

                # Process which deletes old backups
                if record.backup_lifespan_qty > 0:
                    # Retrieve a list of all backup files in the destination_path
                    backup_files = glob.glob(
                        os.path.join(destination_path, "Backup_*.zip")
                    )
                    # Sort backup files based on creation date
                    backup_files.sort(key=os.path.getctime, reverse=True)
                    # Check if file_path is in the backup_files
                    if any(bu_file == file_path for bu_file in backup_files):
                        desired_qty = record.backup_lifespan_qty
                    else:
                        desired_qty = record.backup_lifespan_qty - 1
                    # Calculate the number of backups to keep
                    backups_to_keep = min(desired_qty, len(backup_files))
                    # Iterate over the extra files and remove them
                    for old_backup in backup_files[backups_to_keep:]:
                        os.remove(old_backup)

                result_type = "success"
                result_msg = "Local Backup process executed successfully."
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"FTP Exception: {e}"
                _logger.error(result_msg)

        # SFTP backup
        elif backup_type == "sftp":
            try:
                sftp, transport = server.establish_sftp_connection()
                # Generate backup using the dump_db function
                bu_file_obj = dump_db(db_name, None, extension)
                # Upload the Backup file object to the remote folder
                sftp.putfo(bu_file_obj, file_path)

                # Process which deletes old backups
                if record.backup_lifespan_qty > 0:
                    # Retrieve a list of all backup files in the destination_path on the remote server
                    backup_files = sftp.listdir(destination_path)
                    # Filter files with names starting with 'Backup_' and having the '.zip' extension
                    backup_files = [
                        file
                        for file in backup_files
                        if file.startswith("Backup_") and file.endswith(".zip")
                    ]
                    # Sort backup files based on modification time (latest first)
                    backup_files.sort(
                        key=lambda bu_file: sftp.stat(
                            os.path.join(destination_path, bu_file)
                        ).st_mtime,
                        reverse=True,
                    )
                    # Check if file_name is in the backup_files
                    if any(bu_file == file_name for bu_file in backup_files):
                        desired_qty = record.backup_lifespan_qty
                    else:
                        desired_qty = record.backup_lifespan_qty - 1
                    # Calculate the number of backups to keep
                    backups_to_keep = min(desired_qty, len(backup_files))
                    # Iterate over the extra files and remove them
                    for old_backup in backup_files[backups_to_keep:]:
                        sftp.remove(os.path.join(destination_path, old_backup))

                sftp.close()
                transport.close()

                result_type = "success"
                result_msg = "SFTP Backup transference process executed successfully."
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Failed to create and send backup file.\nError: {e}"
                _logger.error(result_msg)

        # Google Drive backup
        elif backup_type == "drive":
            try:
                # Get Google Drive Service
                service = server.provider_authenticate()
                # Generate backup using the dump_db function
                bu_file_obj = dump_db(db_name, None, extension)
                # Create a MediaIoBaseUpload object from the io.BufferedRandom object
                media = server.get_drive_file_media(bu_file_obj, "application/zip")
                # Get the current UTC time in ISO format
                current_time = datetime.now(timezone.utc).isoformat()

                file_metadata = {
                    "name": file_name,
                    "parents": [server.parent_folder],
                    "description": "Uploaded from Odoo",
                    "mimeType": "application/zip",
                    "createdTime": current_time,
                    "modifiedTime": current_time,
                }

                # Create the file
                file = (
                    service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute()
                )

                # Process which deletes old backups
                if record.backup_lifespan_qty > 0:
                    # Retrieve a list of all backup files in the parent folder on Google Drive
                    results = (
                        service.files()
                        .list(
                            q=f"'{server.parent_folder}' in parents and mimeType='application/zip'",
                            fields="files(id, name, createdTime)",
                        )
                        .execute()
                    )
                    backup_files = results.get("files", [])
                    # Sort backup files based on creation time (latest first)
                    backup_files.sort(
                        key=lambda current_file: current_file["createdTime"],
                        reverse=True,
                    )
                    # Check if file['id'] is in the backup_files
                    if any(bu_file.get("id") == file["id"] for bu_file in backup_files):
                        desired_qty = record.backup_lifespan_qty
                    else:
                        desired_qty = record.backup_lifespan_qty - 1
                    # Define the number of backups to keep
                    backups_to_keep = min(desired_qty, len(backup_files))
                    # Iterate over the extra files and remove them
                    for old_backup in backup_files[backups_to_keep:]:
                        service.files().delete(fileId=old_backup["id"]).execute()

                result_type = "success"
                result_msg = f"Google Drive Backup process executed successfully.\nThe file ID is: {file['id']}"
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Google Drive Exception: {e}"
                _logger.error(result_msg)

        # Google Drive backup
        elif backup_type == "dropbox":
            try:
                # Get Dropbox Client
                dbx = server.provider_authenticate()
                # Generate backup using the dump_db function
                bu_file_obj = dump_db(db_name, None, extension)
                # Upload the file content to Dropbox
                file = dbx.files_upload(bu_file_obj.read(), file_path)

                # Process which deletes old backups
                if record.backup_lifespan_qty > 0:
                    # Retrieve a list of all backup files in the Dropbox folder
                    results = dbx.files_list_folder(path=destination_path)
                    backup_files = results.entries
                    # Sort backup files based on server_modified timestamp (latest first)
                    backup_files.sort(
                        key=lambda bu_file: bu_file.server_modified.timestamp(),
                        reverse=True,
                    )
                    # Check if file['id'] is in the backup_files
                    if any(bu_file.id == file.id for bu_file in backup_files):
                        desired_qty = record.backup_lifespan_qty
                    else:
                        desired_qty = record.backup_lifespan_qty - 1
                    # Calculate the number of backups to keep
                    backups_to_keep = min(desired_qty, len(backup_files))
                    # Iterate over the extra files and remove them
                    for old_backup in backup_files[backups_to_keep:]:
                        dbx.files_delete_v2(path=old_backup.path_display)

                result_type = "success"
                result_msg = f"Dropbox Backup process executed successfully.\nThe file ID is: {file.id}"
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Dropbox Exception: {e}"
                _logger.error(result_msg)

        # Unrecognized Backup type scenario
        else:
            result_type = "danger"
            result_msg = (
                f"Failed to execute the automatic backup process for record ID {record.id} due to an "
                f"unrecognized backup type."
            )
            _logger.error(result_msg)

        # Display an alert window for manual execution, or alternatively, send an email if applicable.
        if not self.env.context.get("manual_execution", False):
            time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            record.last_execution_result = (
                f"RESULT TYPE: {result_type}\nDATE (yyyy-mm-dd hh:mm:ss): {time}\n"
                f"DETAILS: {result_msg}"
            )
            record.notify_result(result_type)
            return True
        else:
            return result_type, result_msg

    def manual_execution(self):
        """Execute backup manually.

        Returns:
            dict: Action to display notification with the execution result.
        """
        for record in self:
            record.check_valid_state()
            context = self.env.context.copy()
            context["manual_execution"] = True
            result_type, msg = record.with_context(context)._scheduled_backup_process(
                record.id
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "context": dict(self._context, active_ids=self.ids),
                "params": {
                    "message": _(msg),
                    "type": result_type,
                    "sticky": False,
                },
            }
