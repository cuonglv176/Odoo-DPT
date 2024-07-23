from odoo import models, fields, api, _
from datetime import datetime


class DPTSaleCalculattionLine(models.Model):
    _name = 'dpt.sale.calculation.line'

    parent_id = fields.Many2one('dpt.sale.calculation')
    service_id = fields.Many2one(related='parent_id.service_id')
    service_uom_ids = fields.Many2many(related='service_id.uom_ids')
    qty = fields.Float(string='QTY', default=1)
    uom_id = fields.Many2one('uom.uom', 'Unit', domain="[('id','in',service_uom_ids)]")
    price = fields.Monetary(currency_field='currency_id', string='Price')
    min_price = fields.Monetary(currency_field='currency_id', string='Min Price')
    currency_id = fields.Many2one(related="service_id.currency_id")
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")
    min_amount_total = fields.Monetary(currency_field='currency_id', string="Min Amount Total",
                                       compute="_compute_amount_total")
    pricelist_item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')

    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.price * item.qty if item.price and item.qty else 0
            item.min_amount_total = item.min_price * item.qty if item.min_price and item.qty else 0
