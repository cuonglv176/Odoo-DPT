from odoo import fields, models, api


class DPTServiceManagement(models.Model):
    _inherit = 'dpt.service.management'

    is_purchase_service = fields.Boolean('Is Purchase Service')
