from odoo import models, fields, api, _
from datetime import datetime


class UomUom(models.Model):
    _name = 'uom.uom'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'uom.uom']

    description = fields.Char(string='Description', tracking=True)
    service_ids = fields.Many2many('dpt.service.management', string='Services')
