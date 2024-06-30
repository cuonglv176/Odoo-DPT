# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTVehicleStageLog(models.Model):
    _name = 'dpt.vehicle.stage.log'

    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    shipping_slip_id = fields.Many2one('dpt.shipping.slip', 'Shipping Slip')
    current_stage_id = fields.Many2one('dpt.vehicle.stage', 'Current Stage')
    next_stage_id = fields.Many2one('dpt.vehicle.stage', 'Next Stage')
    log_datetime = fields.Datetime('Log Datetime', default=lambda self: fields.Datetime.now())
    log_time = fields.Float('Log Time')
    description = fields.Text('Description')
