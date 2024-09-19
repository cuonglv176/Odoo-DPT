# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order', string='Đơn hàng', compute="_compute_sale_id", store=True)

    @api.depends('invoice_origin')
    def _compute_sale_id(self):
        for rec in self:
            rec.sale_id = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    service_line_ids = fields.Many2many('dpt.sale.service.management', string='Service Line')
    order_line_ids = fields.Many2many('sale.order.line', string='Order Line')
