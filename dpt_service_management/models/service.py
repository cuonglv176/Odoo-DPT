# custom_service_management/models/service.py

from odoo import models, fields


class DPTService(models.Model):
    _name = 'dpt.service.management'
    _description = 'DPT Service Management'

    code = fields.Char(string='Service Code')
    name = fields.Char(string='Service Name')
    service_type = fields.Char(string='Service Type')
    department = fields.Char(string='Executing Department')
    cost_account = fields.Char(string='Cost Account')
    revenue_account = fields.Char(string='Revenue Account')
    steps = fields.Integer(string='Steps')
