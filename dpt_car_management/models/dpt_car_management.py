# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTCarManagement(models.Model):
    _name = 'dpt.car.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', tracking=True)
    car_type = fields.Char('Car Type', tracking=True)
    car_code = fields.Char('Car Code', tracking=True)
    car_register_code = fields.Char('Car Register Code', tracking=True)
    driver_name = fields.Char('Driver Name', tracking=True)
    driver_phone = fields.Char('Driver Phone', tracking=True)
    image = fields.Image("Image", tracking=True)
    tracking_ids = fields.One2many('dpt.car.tracking', 'car_id', 'Car Tracking')
