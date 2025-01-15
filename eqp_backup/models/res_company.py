# -*- coding: utf-8 -*-

import importlib

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    eqp_backup_enable_local = fields.Boolean(
        string="Activate Local Functionality",
        help="This policy will activate the Local Backup functionality.",
    )
    eqp_backup_enable_sftp = fields.Boolean(
        string="Activate SFTP Functionality",
        help="This policy will activate the Secure File Transfer Protocol (SFTP) transfer functionality.",
    )
    eqp_backup_enable_drive = fields.Boolean(
        string="Activate Google Drive Functionality",
        help="This policy will activate the Google Drive transfer functionality.",
    )
    eqp_backup_enable_dropbox = fields.Boolean(
        string="Activate Dropbox Functionality",
        help="This policy will activate the Dropbox transfer functionality.",
    )

    eqp_backup_enable_success_email = fields.Boolean(
        string="Activate Success Email Notification",
        help="This policy activates automatic email notifications upon successful completion of a backup process.",
    )
    eqp_backup_enable_failure_email = fields.Boolean(
        string="Activate Failure Email Notification",
        help="This policy activates automatic email notifications upon failure of a backup process.",
    )

    eqp_backup_success_email_address = fields.Char(
        string="Additional email addresses for Success Notifications",
        help="By default, the system sends notifications to the responsible user of the backup record. However, "
        "here you can add additional email addresses for notification if needed.",
    )
    eqp_backup_failure_email_address = fields.Char(
        string="Additional email addresses for Failure Notifications",
        help="By default, the system sends notifications to the responsible user of the backup record. However, "
        "here you can add additional email addresses for notification if needed.",
    )

    @api.constrains("eqp_backup_enable_drive", "eqp_backup_enable_dropbox")
    def _check_eqp_backup_enable_drive_dropbox(self):
        for company in self:
            if company.eqp_backup_enable_dropbox:
                try:
                    importlib.import_module("dropbox")
                except ImportError:
                    raise ValidationError(
                        _(
                            'The "eqp_automatic_backup" module requires dropbox for automated backups via Dropbox.\n'
                            "Please install dropbox by running: `sudo pip3 install dropbox`\n"
                            "(recommended version dropbox>=12.0.2)"
                        )
                    )
            if company.eqp_backup_enable_drive:
                try:
                    importlib.import_module("google.oauth2.service_account")
                    importlib.import_module("googleapiclient.discovery")
                except ImportError:
                    raise ValidationError(
                        _(
                            'The "eqp_automatic_backup" module requires googleapiclient package for automated backups via Google Drive.'
                            "\nPlease install google-api-python-client by running: `sudo pip3 install google-api-python-client`"
                            "\n(recommended version google-api-python-client>=2.154.0)"
                        )
                    )
