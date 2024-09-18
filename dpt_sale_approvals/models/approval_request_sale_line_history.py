from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class ApprovalRequestHistory(models.Model):
    _name = 'dpt.approval.request.sale.line.history'

    service_management_id = fields.Many2one('dpt.sale.service.management', string='Dịch vụ')
    approval_id = fields.Many2one('approval.request',string='Phê duyệt')
    new_price = fields.Monetary(currency_field='currency_id', string='Giá mới')
    price = fields.Monetary(currency_field='currency_id', string='Giá cũ')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
