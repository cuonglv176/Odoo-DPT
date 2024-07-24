from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'approval_id', string='Sale Service')
    sale_fields_ids = fields.One2many('dpt.sale.order.fields', 'approval_id', string='Sale Order Fields')
    order_line_ids = fields.One2many('sale.order.line', 'approval_id', string='Sale Order Line')
    sequence_code = fields.Char(string="Code", related='category_id.sequence_code')
    payment_user_type = fields.Selection([
        ('customer', 'Khách hàng'),
        ('company', 'Công ty'),
    ], string='Bên thanh toán')
    active = fields.Boolean('Active', default=True)

    def action_approve(self, approver=None):
        res = super(ApprovalRequest, self).action_approve(approver)
        approver = self.approver_ids.filtered(lambda sp: sp.status == 'approved')
        # if not approver or len(approver) == 1:
        if self.request_status == 'approved':
            self = self.with_context({'final_approved': True})
            for sale_service_id in self.sale_service_ids:
                sale_service_id.price = sale_service_id.new_price
            for order_line_id in self.order_line_ids:
                order_line_id.price_unit = sale_service_id.new_price_unit
        return res

    def action_refuse(self, approver=None):
        res = super(ApprovalRequest, self).action_refuse(approver)
        # approver = self.approver_ids.filtered(lambda sp: sp.status == 'refused')
        if res.status == 'refused':
            res.sale_id.price_status = 'no_price'
            for sale_service_id in self.sale_service_ids:
                sale_service_id.new_price = sale_service_id.price
            for order_line_id in self.order_line_ids:
                order_line_id.new_price_unit = sale_service_id.price_unit
        return res
