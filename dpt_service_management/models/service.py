# custom_service_management/models/service.py

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class DPTServiceType(models.Model):
    _name = 'dpt.service.management.type'
    _description = 'DPT Service Management Type'
    _order = 'create_date DESC'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')


class DPTService(models.Model):
    _name = 'dpt.service.management'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'DPT Service Management'
    _order = 'create_date DESC'

    code = fields.Char(string='Service Code', default='NEW', readonly=True, copy=False, index=True, tracking=True)
    name = fields.Char(string='Service Name', required=True, tracking=True)
    service_type_id = fields.Many2one('dpt.service.management.type', string='Service Type', index=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Executing Department', index=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Default', index=True, tracking=True)
    cost_account_id = fields.Many2one('account.account', string='Cost Account', tracking=True)
    revenue_account_id = fields.Many2one('account.account', string='Revenue Account', tracking=True)
    steps_count = fields.Integer(string='Steps', compute="_compute_count_steps")
    description = fields.Html(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    price = fields.Monetary(currency_field='currency_id', string='Price', tracking=True)
    uom_id = fields.Many2one('uom.uom', string='Default Unit', tracking=True)
    uom_ids = fields.Many2many('uom.uom', string='Units', tracking=True)
    is_create_ticket = fields.Boolean('Create Ticket', tracking=True)
    steps_ids = fields.One2many('dpt.service.management.steps', 'service_id', string='Steps', copy=True, auto_join=True,
                                tracking=True)
    required_fields_ids = fields.One2many('dpt.service.management.required.fields', 'service_id',
                                          string='Required Fields', copy=True, auto_join=True, tracking=True)
    active = fields.Boolean('Active', default='True')

    _sql_constraints = [
        ('code_name_index', 'CREATE INDEX code_name_index ON dpt_service_management (code, name)',
         'Index on code and name')
    ]

    @api.depends('steps_ids')
    def _compute_count_steps(self):
        for rec in self:
            rec.steps_count = len(rec.steps_ids)

    @api.model
    def create(self, vals):
        if vals.get('code', 'NEW') == 'NEW':
            vals['code'] = self._generate_service_code()
        return super(DPTService, self).create(vals)

    def _generate_service_code(self):
        sequence = self.env['ir.sequence'].next_by_code('dpt.service.management') or '00'
        return f'{sequence}'


class DPTServiceSteps(models.Model):
    _name = 'dpt.service.management.steps'
    _description = 'DPT Service Management Steps'
    _order = 'sequence ASC'

    sequence = fields.Integer(string='Sequence')
    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2one('hr.employee', string='Employee Default')
    description = fields.Html(string='Description')
    is_create_ticket = fields.Boolean('Create Ticket')
    service_id = fields.Many2one('dpt.service.management', string='Service', ondelete='cascade')


class RequiredField(models.Model):
    _name = 'dpt.service.management.required.fields'
    _description = 'DPT Service Management required fields'
    _order = 'create_date DESC'

    fields_id = fields.Many2one('ir.model.fields', string='Field')
    field = fields.Selection([
        ('address', 'Address'),
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('distance', 'Distance'),
        ('other', 'Other'),
    ], string='Field Mapping', default='other')
    name = fields.Char(string='Name')
    description = fields.Html(string='Description')
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
        ('selection', 'Selection')
    ], string='Fields type', default='char')
    selection_value_ids = fields.One2many('dpt.sale.order.fields.selection','fields_id', string='Selection Value')
    type = fields.Selection(selection=[
        ("required", "Required"),
        ("options", "Options")
    ], string='Type Fields', default='options')
    service_id = fields.Many2one('dpt.service.management', string='Service', ondelete='cascade')
    using_calculation_price = fields.Boolean('Using Calculation Price')
    uom_id = fields.Many2one('uom.uom', 'Unit')


class SaleOrderFieldSelection(models.Model):
    _name = 'dpt.sale.order.fields.selection'

    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    name = fields.Char('Selection Value')