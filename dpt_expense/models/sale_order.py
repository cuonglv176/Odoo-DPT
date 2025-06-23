# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    expense_amount_total = fields.Monetary('Tổng doanh thu tính chi phí', compute="compute_expense_amount_total")
    allocated_amount_total = fields.Monetary('Chi phí đã phân bổ', compute="compute_allocated_amount_total")

    @api.depends('sale_service_ids')
    def compute_expense_amount_total(self):
        for order in self:
            order.expense_amount_total = sum(order.service_combo_ids.filtered(
                lambda
                    x: x.compute_uom_id and x.compute_uom_id.use_for_allocate_expense and x.combo_id and x.combo_id.use_for_allocate_expense).mapped(
                'amount_total'))

    def compute_allocated_amount_total(self):
        for order in self:
            move_line_ids = self.env['account.move.line'].sudo().search(
                [('sale_order_id', '=', order.id), ('move_id.state', '=', 'posted')])
            order.allocated_amount_total = sum(move_line_ids.mapped('debit'))
