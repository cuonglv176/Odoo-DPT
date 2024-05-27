# custom_service_management/models/service.py

from odoo import models, fields, api, _
from datetime import datetime


class DPTServiceType(models.Model):
    _name = 'dpt.service.management.type'
    _description = 'DPT Service Management Type'
    _order = 'create_date DESC'

    name = fields.Char(string='Name')


class DPTService(models.Model):
    _name = 'dpt.service.management'
    _description = 'DPT Service Management'
    _order = 'create_date DESC'

    code = fields.Char(string='Service Code', default='NEW', readonly=True, copy=False)
    name = fields.Char(string='Service Name', required=True)
    service_type_id = fields.Many2one('dpt.service.management.type', string='Service Type')
    department = fields.Many2one('hr.department', string='Executing Department')
    cost_account_id = fields.Many2one('account.account', string='Cost Account')
    revenue_account_id = fields.Many2one('account.account', string='Revenue Account')
    steps_count = fields.Integer(string='Steps')

    _sql_constraints = [
        ('code_name_index', 'CREATE INDEX code_name_index ON dpt_service_management (code, name)',
         'Index on code and name')
    ]

    @api.model
    def create(self, vals):
        if vals.get('code', 'NEW') == 'NEW':
            vals['code'] = self._generate_service_code()
        return super(DPTService, self).create(vals)

    def _generate_service_code(self):
        sequence = self.env['ir.sequence'].next_by_code('dpt.service.management') or '00'
        return f'{sequence}'
