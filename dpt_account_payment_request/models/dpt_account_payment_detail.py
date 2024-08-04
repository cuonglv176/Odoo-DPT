from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DPTAccountPaymentDetail(models.Model):
    _name = 'dpt.account.payment.detail'
    _description = 'DPT Account Payment Detail'

    payment_id = fields.Many2one('Account Payment', string='Payment')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY', default=1)
    uom_id = fields.Many2one('uom.uom', string='Uom')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    price_cny = fields.Monetary(currency_field='currency_cny_id', string='Price CNY')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")

    @api.onchange('price', 'qty', 'price_cny')
    def onchange_update_amount_payment(self):
        amount = 0
        for detail_id in self.payment_id.detail_ids:
            amount += detail_id.amount_total
        self.payment_id.amount = amount
        
    @api.onchange('price_cny')
    def onchange_price_cny(self):
        self.price = self.price_cny * self.currency_cny_id.rate

    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.qty * item.price * item.compute_value if item.pricelist_item_id.is_price and item.pricelist_item_id.compute_price == 'table' else item.qty * item.price

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = self.price * self.qty * self.compute_value if self.pricelist_item_id.is_price and self.pricelist_item_id.compute_price == 'table' else self.qty * self.price
