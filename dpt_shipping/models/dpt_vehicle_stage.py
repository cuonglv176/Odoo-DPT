# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTVehicleStage(models.Model):
    _name = 'dpt.vehicle.stage'
    _order = 'sequence'

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')
    is_default = fields.Boolean('Is Default')

