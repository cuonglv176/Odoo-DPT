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
import io
import json
import base64
import logging

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)

try:
    from paramiko import Transport, SFTPClient, AuthenticationException

except ImportError:
    raise ImportError(
        'The "eqp_automatic_backup" module requires paramiko for automated backups via SFTP.\n'
        "Please install paramiko by running: `sudo pip3 install paramiko`\n"
        "(recommended version paramiko>=3.5.0)"
    )

# Constants Declaration
SCOPES = ["https://www.googleapis.com/auth/drive"]


# Static Functions


def get_credentials_data(credentials_content):
    """
    Parse and return credentials data from the given content.

    Args:
        credentials_content (str): Content of the credential file.

    Returns:
        dict or str: Parsed credentials data.
    """
    try:
        # Assuming the content is a dictionary
        credentials_data = json.loads(credentials_content)
    except json.JSONDecodeError as e:
        # Handle the case where the file is not a valid JSON
        raise ValidationError(f"error Invalid JSON format. Error:{str(e)}")
    return credentials_data


# Model `BackupServer`
class BackupServer(models.Model):
    """
    Model to manage backup servers and their configurations.
    """

    _name = "backup.server"
    _description = "Backup Servers"
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

    name = fields.Char(string="Name", required=True, tracking=True, help="Record Name")
    description = fields.Text(
        string="Description", copy=False, help="Add a brief description of the record"
    )
    state = fields.Selection(
        [
            ("draft", "Not Confirmed"),
            ("confirmed", "Confirmed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        tracking=True,
        copy=False,
        help="Backup Server Status",
    )

    backup_type = fields.Selection(
        [
            ("local", "Local"),
            ("sftp", "SFTP"),
            ("drive", "Google Drive"),
            ("dropbox", "Dropbox"),
        ],
        string="Backup Type",
        copy=False,
        tracking=True,
        help="Select the Backup type:"
        "\nLocal: Save in the local server."
        "\nSFTP: Send the backup to an SFTP server."
        "\nG. Drive: Send to a Google Drive Folder."
        "\nDropbox: Send to a Dropbox Folder.",
    )
    destination_path = fields.Char(
        string="Destination Path",
        tracking=True,
        copy=False,
        help="Put the full backup destination path route.",
    )
    # SFTP SERVER FIELDS
    server_address = fields.Char(string="Address", tracking=True, help="Server Address")
    server_port = fields.Char(string="Port", tracking=True, size=5, help="Server Port")
    server_user = fields.Char(string="User", tracking=True, help="Server User")
    server_password = fields.Char(string="Password", help="Server Password")
    # GOOGLE DRIVE FIELDS
    drive_credentials_type = fields.Selection(
        [("file", "Upload Credentials File"), ("text", "Enter Credentials Directly")],
        string="Credentials Type",
        tracking=True,
        help="Choose the type of input for save your Credentials:\n"
        "- Upload Credentials File: Select and upload your service account key "
        "file in .json format for G. Drive. Or .txt for Dropbox.\n"
        "- Enter Credentials Directly: Manually type the credentials directly into"
        " a text field, respecting the JSON structure format for G. Drive. "
        "Or plain text for Dropbox .",
    )
    drive_credentials_file = fields.Binary(
        string="Credentials File",
        attachment=True,
        help="Upload your service account key file:\n"
        "- .json extension for Google Drive.\n"
        "- .txt extension for Dropbox",
    )
    drive_credentials_file_name = fields.Char(string="Credentials File Name")
    drive_credentials_input = fields.Text(
        string="Credentials Input",
        help="Enter your service account key directly:\n"
        "- JSON format for Google Drive.\n"
        "- Plain Text for Dropbox.",
    )
    # DROPBOX FIELDS
    dropbox_app_key = fields.Char(string="App Key", help="Dropbox APP Key")
    dropbox_app_secret = fields.Char(string="App Secret", help="Dropbox APP Secret")
    dropbox_app_token = fields.Char(
        string="App Token", readonly=True, help="Dropbox APP Token"
    )

    parent_folder = fields.Char(
        string="Parent Folder ID",
        tracking=True,
        help="Parent Folder ID.\n(to get this ID open the folder on Google Drive and copy it "
        "from the web URL)",
    )
    credentials_ok = fields.Boolean(
        string="Credentials Validation", compute="_compute_credentials_ok"
    )
    record_ids = fields.One2many("backup.record", "server_id", string="Related Records")

    _sql_constraints = [
        ("name_unique", "unique(name, company_id)", "A unique name per company.")
    ]

    def write(self, vals):
        """
        Overrides the write method to update the state based on the 'active' field.

        Args:
            vals (dict): Values to write.

        Returns:
            dict: Written values.
        """
        # Update State.
        if "active" in vals:
            vals["state"] = "draft" if vals["active"] is True else "archived"
        return super(BackupServer, self).write(vals)

    def copy(self, default=None):
        self.ensure_one()
        chosen_name = default.get("name") if default else ""
        new_name = chosen_name or _("%s (copy)", self.name)
        default = dict(default or {}, name=new_name)
        return super(BackupServer, self).copy(default)

    def _compute_drive_credentials_file_name(self):
        """
        Computes and sets the credential file name based on server details.
        """
        for server in self:
            server.drive_credentials_file_name = (
                f"{server.id_client}_{server.edi_identification}.key"
            )

    @api.depends(
        "backup_type",
        "destination_path",
        "server_address",
        "server_user",
        "server_port",
        "server_password",
        "parent_folder",
        "drive_credentials_type",
        "drive_credentials_file",
        "drive_credentials_input",
        "dropbox_app_key",
        "dropbox_app_secret",
        "dropbox_app_token",
    )
    def _compute_credentials_ok(self):
        """
        Computes the value of 'credentials_ok' field based on the backup type and associated credentials.
        """
        for server in self:

            credentials_ok = False
            backup_type = server.backup_type

            if backup_type == "local":
                credentials_ok = True if server.destination_path else False
            elif backup_type == "sftp":
                credentials_ok = (
                    server.server_address
                    and server.server_user
                    and server.server_port
                    and server.server_password
                )
            elif backup_type == "drive":
                credentials_ok = (
                    server.parent_folder
                    and (
                        server.drive_credentials_type == "file"
                        and server.drive_credentials_file
                    )
                    or (
                        server.drive_credentials_type == "text"
                        and server.drive_credentials_input
                    )
                )
            elif backup_type == "dropbox":
                credentials_ok = (
                    server.dropbox_app_key
                    and server.dropbox_app_secret
                    and server.dropbox_app_token
                )

            server.credentials_ok = credentials_ok

    def revert_state(self):
        """
        Reverts the state of the server and associated records to 'draft'.
        """
        for server in self:
            if server.state == "confirmed":
                server.write({"state": "draft"})
                records = server.record_ids and server.record_ids.filtered(
                    lambda r: r.state == "confirmed"
                )
                if records:
                    records.update_cron_state(False)
                    records.write({"state": "paused"})

    def check_company_policy(self):
        """
        Checks company policy for enabling backup types.

        Raises:
            ValidationError: If the policy is not enabled for the selected backup type.
        """
        company_id = self.company_id or self.env.company
        backup_type = self.backup_type
        if (
            (backup_type == "local" and not company_id.eqp_backup_enable_local)
            or (backup_type == "sftp" and not company_id.eqp_backup_enable_sftp)
            or (backup_type == "drive" and not company_id.eqp_backup_enable_drive)
            or (backup_type == "dropbox" and not company_id.eqp_backup_enable_dropbox)
        ):
            policy_warning = backup_type.capitalize()
            raise ValidationError(
                f"You cannot use this functionality without the {policy_warning} policy enabled."
            )

    @api.onchange("backup_type")
    def _onchange_backup_type(self):
        """
        Onchange method to validate a backup type based on company policies.
        """
        self.check_company_policy()

    def confirm(self):
        """
        Confirms the server, updating the state and associated records.
        """
        for server in self:
            server.check_company_policy()
            # Update State to confirm
            server.write({"state": "confirmed"})
            records = server.record_ids and server.record_ids.filtered(
                lambda r: r.state == "paused"
            )
            if records:
                records.update_cron_state(True)
                records.write({"state": "confirmed"})

    def generate_dropbox_token(self):
        """
        Generates a Dropbox token using the provided credentials.

        Returns:
            dict: Action dictionary to open the Dropbox Token Assignment wizard.

        Raises:
            ValidationError: If the credentials are missing or if an error occurs during token generation.
        """
        self.ensure_one()

        dropbox_app_key = self.dropbox_app_key
        dropbox_app_secret = self.dropbox_app_secret
        if not dropbox_app_key or not dropbox_app_secret:
            raise ValidationError(
                "Error: Missing credentials. Please ensure that all the following credentials are "
                "set: APP Key, Secret, and Token."
            )
        else:
            try:
                import dropbox

                dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
                    dropbox_app_key, dropbox_app_secret, token_access_type="offline"
                )
                dbx_auth_url = dbx_auth.start()
            except Exception as e:
                raise ValidationError(f"Error: {e}.")

            return {
                "type": "ir.actions.act_window",
                "name": "Dropbox Token Assignment",
                "res_model": "backup.dropbox.token.assignment.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_dropbox_auth_url": dbx_auth_url,
                    "default_server_id": self.id,
                },
            }

    def establish_sftp_connection(self):
        """
        Establishes an SFTP connection to the server.

        Returns:
            tuple: Tuple containing SFTP connection and transport objects.
        """
        for server in self:
            # Set SFTP connection parameters
            sftp_host = server.server_address
            sftp_port = int(server.server_port)
            sftp_user = server.server_user
            sftp_password = server.server_password

            # Establish an SFTP connection
            transport = Transport((sftp_host, sftp_port))
            transport.connect(username=sftp_user, password=sftp_password)

            sftp_connection = SFTPClient.from_transport(transport)

            return sftp_connection, transport

    def get_file_path_details(self, name, extension):
        """
        Validates the extension and formats file path details.

        Args:
            name (str): Name of the file.
            extension (str): File extension.

        Returns:
            tuple: Tuple containing destination path and formatted file name.
        """
        # Validate the extension
        if extension not in ("txt", "zip"):
            _logger.error("Unsupported file extension (supported formats: txt, zip)")
            raise ValidationError(
                "Unsupported file extension (supported formats: txt, zip)"
            )
        # Catching and formatting timestamp
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        formatted_date = now.strftime("%Y-%m-%d_%H.%M.%S")
        file_name = f"Backup_{name}_{formatted_date}.{extension}"
        destination_path = (
            self.destination_path
            if self.destination_path and self.destination_path.endswith("/")
            else (self.destination_path or "") + "/"
        )

        return destination_path, file_name

    def get_drive_file_media(self, f_content, m_type):
        """
        Returns a MediaIoBaseUpload object for Google Drive file upload.

        Args:
            f_content (io.BytesIO): File-like object containing the file content.
            m_type (str): Mime type of the file.

        Returns:
            MediaIoBaseUpload: Media upload object.
        """
        from googleapiclient.http import MediaIoBaseUpload

        return MediaIoBaseUpload(f_content, mimetype=m_type, resumable=True)

    def provider_authenticate(self):
        """Authenticate with the backup provider and return the service object.

        Returns:
            object: Service object for the backup provider.
        """
        self.ensure_one()
        credentials_data = None
        backup_type = self.backup_type

        # Validate type
        if backup_type not in ("drive", "dropbox"):
            raise ValidationError("Error, Invalid backup type specified.")

        # If Google Drive Backup Type
        if backup_type == "drive":
            # File Upload
            if self.drive_credentials_type == "file":
                creds_file = self.drive_credentials_file
                if creds_file:
                    credentials_content = base64.b64decode(creds_file)
                    credentials_data = get_credentials_data(credentials_content)
                else:
                    raise ValidationError("Error, No credentials file uploaded")
            # Text Input
            elif self.drive_credentials_type == "text":
                creds_input = self.drive_credentials_input
                if creds_input:
                    credentials_data = get_credentials_data(creds_input)
                else:
                    raise ValidationError(
                        "Error, No valid or empty credentials text input"
                    )
        else:
            if (
                self.dropbox_app_key
                and self.dropbox_app_secret
                and self.dropbox_app_token
            ):
                credentials_data = (
                    self.dropbox_app_key,
                    self.dropbox_app_secret,
                    self.dropbox_app_token,
                )
            else:
                raise ValidationError(
                    "Error: Missing or empty credentials. Please ensure that all the following "
                    "credentials are set: APP Key, Secret, and Token."
                )
        # Get Service
        try:
            if backup_type == "drive":
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                creds = service_account.Credentials.from_service_account_info(
                    credentials_data, scopes=SCOPES
                )
                service = build("drive", "v3", credentials=creds)
            else:
                import dropbox

                service = dropbox.Dropbox(
                    app_key=credentials_data[0],
                    app_secret=credentials_data[1],
                    oauth2_refresh_token=credentials_data[2],
                )
        except Exception as e:
            raise ValidationError(
                f"Failed to initialize {backup_type} service. Error: {e}"
            )

        return service

    def test_connection(self):
        """Test the connection to the backup provider and display the result.

        Returns:
            dict: Action to display notification with the test result.
        """
        self.ensure_one()
        self.check_company_policy()

        # Set a warning notification values by default
        result_type = "warning"
        result_msg = (
            "There was an internal issue. You Can not test connection for a backup type different of SFTP, "
            "G.Drive or Dropbox."
        )

        # Test SFTP Connection
        if self.backup_type == "sftp":
            try:
                sftp, transport = self.establish_sftp_connection()
                # Close SFTP Connection
                sftp.close()
                transport.close()
                # Provide a successful test result values
                result_type = "success"
                result_msg = "The SFTP connection was successful."
                _logger.info(result_msg)

            except AuthenticationException as auth_error:
                # Set a warning notification values due to an authentication error
                result_msg = f"The SFTP connection failed due to authentication error.\nError: {auth_error}"
                _logger.error(result_msg)

            except Exception as e:
                # Set s danger notification values due to a failed test
                result_type = "danger"
                result_msg = f"The SFTP connection failed. Error: {e}"
                _logger.error(result_msg)

        # Test Google Drive Connection
        if self.backup_type == "drive":
            try:
                service = self.provider_authenticate()
                about = service.about().get(fields="user, storageQuota").execute()
                # Provide a successful test result values
                result_type = "success"
                result_msg = (
                    "Google Drive Connection Successful!\n"
                    f"User: {about['user']['displayName']}"
                )
                _logger.info(result_msg)
            except Exception as e:
                result_type = "danger"
                result_msg = f"Google Drive Connection Failed. Error: {e}"
                _logger.error(result_msg)

        # Test Dropbox Connection
        if self.backup_type == "dropbox":
            try:
                dbx = self.provider_authenticate()
                account_info = dbx.users_get_current_account()
                # Provide a successful test result values
                result_type = "success"
                result_msg = (
                    "Dropbox Connection Successful!\n"
                    f"Account: {account_info.account_id[:8]}..."
                )
                _logger.info(result_msg)
            except Exception as e:
                result_type = "danger"
                result_msg = f"Dropbox Connection Failed. Error: {e}"
                _logger.error(result_msg)

        if result_type == "success":
            # Update State if the confirmation flag is true
            if self.env.context.get("confirm", False):
                self.confirm()

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

    def send_test_file(self):
        """
        Sends a test file to the backup destination and displays the result.

        Returns:
            dict: Action to display notification with the test result.
        """
        self.ensure_one()
        # Set a warning notification values by default (Display just on a strange case).
        result_type = "warning"
        result_msg = "There was an internal issue. Please contact the system administrator for assistance."

        # Define the file path and content
        file_content = "This is a test file created by eqp_backups module just for testing purposes"
        f_path, f_name = self.get_file_path_details("test", "txt")
        file_path = f_path + f_name

        backup_type = self.backup_type

        # Test Local File transfer
        if backup_type == "local":
            try:
                # Check if the file path exists
                if not os.path.isdir(f_path):
                    # Try to create it if it does not exist
                    os.makedirs(f_path)
                # Open the file with write permissions
                file = open(file_path, "w")
                # Write file content
                file.write(file_content)
                # Closing the file
                file.close()
                # Provide a successful test result values
                result_type = "success"
                result_msg = "The Local file transference was successful."
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Failed to create test file.\nError: {e}"
                _logger.error(result_msg)

        # Test SFTP File transfer
        elif backup_type == "sftp":
            try:
                # Get SFTP Connection Params
                sftp, transport = self.establish_sftp_connection()

                # Upload the file to the server
                with sftp.file(file_path, "w") as f:
                    f.write(file_content)
                # Close SFTP Connection
                sftp.close()
                transport.close()
                # Provide a successful test result values
                result_type = "success"
                result_msg = "The SFTP file transference was successful."
                _logger.info(result_msg)

            except AuthenticationException as auth_error:
                # Set a warning notification values due to an authentication error
                result_msg = f"The SFTP transfer test failed due to authentication error.\nError: {auth_error}"
                _logger.error(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Failed to create and send test file.\nError: {e}"
                _logger.error(result_msg)

        # Test Google Drive File transfer
        elif backup_type == "drive":
            if not self.parent_folder:
                raise ValidationError(
                    "Error: Parent Folder ID not found. Please provide a valid parent folder ID."
                )
            try:
                # Ensure file_content is encoded to bytes
                file_content_bytes = (
                    file_content.encode("utf-8")
                    if isinstance(file_content, str)
                    else file_content
                )
                # Create a file-like object from the byte content
                media = self.get_drive_file_media(
                    io.BytesIO(file_content_bytes), "application/txt"
                )
                # Get the current UTC time in ISO format
                current_time = datetime.now(timezone.utc).isoformat()

                # Fill file metadata
                file_metadata = {
                    "name": f_name,
                    "parents": [self.parent_folder],
                    "description": "Uploaded from Odoo",
                    "mimeType": "application/txt",
                    "createdTime": current_time,
                    "modifiedTime": current_time,
                }
                # Get Google Drive Service
                service = self.provider_authenticate()
                # Create the file
                file = (
                    service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute()
                )

                # Provide a successful test result values
                result_type = "success"
                result_msg = f"The Google Drive test file transference was successful.\nThe file ID is: {file['id']}"
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Error transferring file to Google Drive: {e}"
                _logger.error(result_msg)

        # Test Google Drive File transfer
        elif backup_type == "dropbox":
            try:
                # Ensure file_content is encoded to bytes
                file_content_bytes = (
                    file_content.encode("utf-8")
                    if isinstance(file_content, str)
                    else file_content
                )
                # Get a Dropbox client
                dbx = self.provider_authenticate()
                # Upload the file content to Dropbox
                with io.BytesIO(file_content_bytes) as file_content_stream:
                    file = dbx.files_upload(file_content_stream.read(), file_path)

                # Provide a successful test result values
                result_type = "success"
                result_msg = f"The Dropbox test file transference was successful.\nThe file ID is: {file.id}"
                _logger.info(result_msg)

            except Exception as e:
                result_type = "danger"
                result_msg = f"Error transferring file to Dropbox: {e}"
                _logger.error(result_msg)

        # Provide feedback
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "context": dict(self._context, active_ids=self.ids),
            "params": {
                "message": _(result_msg),
                "type": result_type,
                "sticky": False,
            },
        }
