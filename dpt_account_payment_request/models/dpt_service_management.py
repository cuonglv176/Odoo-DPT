from odoo import models, fields, api, _


class DPTService(models.Model):
    _inherit = 'dpt.service.management'

    account_payment_type_id = fields.Many2one('dpt.account.payment.type', string='Loại ĐNTT mặc định')