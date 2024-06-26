# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTCarTracking(models.Model):
    _name = 'dpt.car.tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    picking_id = fields.Many2one('stock.picking', 'Picking')
    car_id = fields.Many2one('dpt.car.management', 'Car')
    description = fields.Text('Description')
    duration = fields.Float('Duration')
