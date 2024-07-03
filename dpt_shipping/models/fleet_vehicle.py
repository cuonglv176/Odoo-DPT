# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    country = fields.Selection([
        ('chinese', 'Chinese'),
        ('vietnamese', 'Vietnamese'),
    ], default='chinese', string='Country')
