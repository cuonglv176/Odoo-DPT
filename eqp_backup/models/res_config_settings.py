# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    eqp_backup_enable_local = fields.Boolean(
        related="company_id.eqp_backup_enable_local", readonly=False
    )
    eqp_backup_enable_sftp = fields.Boolean(
        related="company_id.eqp_backup_enable_sftp", readonly=False
    )
    eqp_backup_enable_drive = fields.Boolean(
        related="company_id.eqp_backup_enable_drive", readonly=False
    )
    eqp_backup_enable_dropbox = fields.Boolean(
        related="company_id.eqp_backup_enable_dropbox", readonly=False
    )

    eqp_backup_enable_success_email = fields.Boolean(
        related="company_id.eqp_backup_enable_success_email", readonly=False
    )
    eqp_backup_enable_failure_email = fields.Boolean(
        related="company_id.eqp_backup_enable_failure_email", readonly=False
    )

    eqp_backup_success_email_address = fields.Char(
        related="company_id.eqp_backup_success_email_address", readonly=False
    )
    eqp_backup_failure_email_address = fields.Char(
        related="company_id.eqp_backup_failure_email_address", readonly=False
    )
