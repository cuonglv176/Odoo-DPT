# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    car_id = fields.Many2one('dpt.car.management', 'Car')
    car_tracking_ids = fields.One2many('dpt.car.tracking', 'picking_id', 'Car Tracking')
