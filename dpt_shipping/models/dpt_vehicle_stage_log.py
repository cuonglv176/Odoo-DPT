# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTVehicleStageLog(models.Model):
    _name = 'dpt.vehicle.stage.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', tracking=True)
    shipping_slip_id = fields.Many2one('dpt.shipping.slip', 'Shipping Slip')
    current_stage_id = fields.Many2one('dpt.vehicle.stage', 'Current Stage', tracking=True)
    next_stage_id = fields.Many2one('dpt.vehicle.stage', 'Next Stage', tracking=True)
    log_datetime = fields.Datetime('Log Datetime', default=lambda self: fields.Datetime.now(), tracking=True)
    log_time = fields.Float('Log Time', tracking=True)
    description = fields.Text('Description', tracking=True)
