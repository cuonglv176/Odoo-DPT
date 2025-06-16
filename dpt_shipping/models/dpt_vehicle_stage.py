# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTVehicleStage(models.Model):
    _name = 'dpt.vehicle.stage'
    _order = 'sequence'

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')
    is_default = fields.Boolean('Is Default')
    country = fields.Selection([
        ('chinese', 'Chinese'),
        ('vietnamese', 'Vietnamese'),
    ], default='chinese', string='Country')
    active = fields.Boolean('Active', default=True)
    is_draft_stage = fields.Boolean('Is Draft Stage')
    is_ready_stage = fields.Boolean('Is Ready Stage')
    is_finish_stage = fields.Boolean('Là trạng thái hoàn thành')

