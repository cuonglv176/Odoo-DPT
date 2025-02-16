# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.lot'

    weight = fields.Float('Weight (kg)', tracking=True)
    volume = fields.Float('Volume (m3)', tracking=True, digits=(12, 5))
    total_weight = fields.Float('Total Weight (kg)', tracking=True, digits=(12, 2))
    total_volume = fields.Float('Total Volume (m3)', tracking=True, digits=(12, 3))

