from odoo import models, fields, api, _
from datetime import datetime


class DPTSaleCalculattionLine(models.Model):
    _name = 'dpt.sale.calculation.line'

    parent_id = fields.Many2one('dpt.sale.calculation')
    service_id = fields.Many2one(related='parent_id.service_id')
    service_uom_ids = fields.Many2many(related='service_id.uom_ids')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one('uom.uom', 'Unit', domain="[('id','in',service_uom_ids)]")
    price = fields.Monetary(currency_field='currency_id', string='Price')
    min_price = fields.Monetary(currency_field='currency_id', string='Min Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total")
    min_amount_total = fields.Monetary(currency_field='currency_id', string="Min Amount Total")

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = (self.price * self.qty)

    @api.onchange('min_price', 'qty')
    def onchange_min_amount_total(self):
        if self.min_price and self.qty:
            self.amount_total = self.min_price * self.qty
