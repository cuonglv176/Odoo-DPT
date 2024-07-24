# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import format_date, frozendict


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    advance_payment_method = fields.Selection(
        selection=[
            ('delivered', "All"),
            ('percentage', "Multiple times (percentage)"),
            ('fixed', "Multiple times (fixed amount)"),
        ],
        string="Create Invoice",
        default='delivered',
        required=True,
        help="A standard invoice is issued with all the order lines ready for invoicing,"
             "according to their invoicing policy (based on ordered or delivered quantity).")
    picking_ids = fields.Many2many('stock.picking', string='Picking')

    @api.onchange('sale_order_ids')
    def onchange_picking(self):
        val_picking_ids = []
        for sale_order_id in self.sale_order_ids:
            picking_ids = self.env['stock.picking'].search([('sale_id', '=', sale_order_id.id)])
            for picking_id in picking_ids:
                val_picking_ids.append(picking_id.id)
        self.picking_ids = [(6, 0, val_picking_ids)]
