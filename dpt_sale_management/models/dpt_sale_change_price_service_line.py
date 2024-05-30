from odoo import models, fields, api, _
from datetime import datetime


class DPTSaleChangePriceServiceLine(models.Model):
    _name = 'dpt.sale.change.price.service.line'

    parent_id = fields.Many2one('dpt.sale.change.price')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    qty = fields.Float(string='QTY')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    change_price = fields.Monetary(currency_field='currency_id', string='Change Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")
