# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    shipping_slip_ids = fields.Many2many('dpt.shipping.slip', string="Phiếu vận chuyển")
    order_expense_ids = fields.Many2many('sale.order', 'purchase_order_expense_rel', 'purchase_id', 'sale_id',
                                         string="Đơn hàng chi phí")
    total_order_expense_ids = fields.Many2many('sale.order', string="Tât cả đơn hàng tính chi phí", store=True,
                                               compute="_compute_order_expense", inverse="_inverse_order_expense")

    @api.depends('shipping_slip_ids')
    def _compute_order_expense(self):
        for item in self:
            item.total_order_expense_ids = item.shipping_slip_ids.mapped('sale_ids')

    def _inverse_order_expense(self):
        pass
