from odoo import api, fields, models, _


class DPTServiceManagement(models.Model):
    _inherit = "dpt.service.management"

    approver_price_list_ids = fields.One2many('dpt.approval.sale.price', 'service_id', string='Approvers')