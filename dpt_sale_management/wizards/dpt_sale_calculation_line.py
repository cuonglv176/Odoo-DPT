from odoo import models, fields, api, _
from datetime import datetime


class DPTSaleCalculattionLine(models.Model):
    _name = 'dpt.sale.calculation.line'

    parent_id = fields.Many2one('dpt.sale.calculation')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one('uom.uom')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")
