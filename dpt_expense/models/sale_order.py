# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    expense_amount_total = fields.Monetary('Tổng doanh thu tính chi phí', compute="compute_expense_amount_total")

    @api.depends('sale_service_ids')
    def compute_expense_amount_total(self):
        for order in self:
            order.expense_amount_total = sum(order.sale_service_ids.filtered(
                lambda x: x.compute_uom_id and x.compute_uom_id.use_for_allocate_expense).mapped('amount_total'))
