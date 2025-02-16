# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    weight = fields.Float('Weight (kg)', related="lot_id.weight")
    volume = fields.Float('Volume (m3)', related="lot_id.volume")
    total_weight = fields.Float('Total Weight (kg)', related="lot_id.total_weight")
    total_volume = fields.Float('Total Volume (m3)', related="lot_id.total_volume")

