# custom_service_management/models/service.py

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals_list):
        res = super(MailMessage, self).create(vals_list)
        if res.model and res.model in ('dpt.service.management.steps', 'dpt.service.management.required.fields'):
            obj_data = self.env[res.model].browse(res.res_id)
            res.res_id = obj_data.service_id.id
            res.model = 'dpt.service.management'
        if res.model and res.model in ('uom.uom'):
            obj_data = self.env[res.model].browse(res.res_id)
            res.res_id = obj_data.service_ids[:1].id
            res.model = 'dpt.service.management'
        return res


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

    code = fields.Char(string='Service Code', default='NEW', copy=False, index=True, tracking=True)
    name = fields.Char(string='Service Name', required=True, tracking=True)
    service_type_id = fields.Many2one('dpt.service.management.type', string='Service Type', index=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Executing Department', index=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Default', index=True, tracking=True)
    cost_account_id = fields.Many2one('account.account', string='Cost Account', tracking=True)
    revenue_account_id = fields.Many2one('account.account', string='Revenue Account', tracking=True)
    steps_count = fields.Integer(string='Steps', compute="_compute_count_steps")
    description = fields.Text(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    price = fields.Monetary(currency_field='currency_id', string='Price', tracking=True)
    uom_id = fields.Many2one('uom.uom', string='Default Unit', tracking=True)
    uom_ids = fields.Many2many('uom.uom', string='Units')
    is_create_ticket = fields.Boolean('Create Ticket', tracking=True)
    steps_ids = fields.One2many('dpt.service.management.steps', 'service_id', string='Steps', copy=True, auto_join=True)
    required_fields_ids = fields.One2many('dpt.service.management.required.fields', 'service_id',
                                          string='Required Fields', copy=True, auto_join=True)
    active = fields.Boolean('Active', default='True')
    # image = fields.Image("Image", required=True, tracking=True)

    _sql_constraints = [
        ('code_name_index', 'CREATE INDEX code_name_index ON dpt_service_management (code, name)',
         'Index on code and name'),
        ('code_uniq', 'unique (code)', "Code already exists!")
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
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'DPT Service Management Steps'
    _order = 'sequence ASC'

    sequence = fields.Integer(string='Sequence', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Default', tracking=True)
    description = fields.Text(string='Description')
    is_create_ticket = fields.Boolean('Create Ticket', tracking=True)
    service_id = fields.Many2one('dpt.service.management', string='Service', ondelete='cascade', tracking=True)

    def unlink(self):
        # log to front end of deleted bookings
        mapping_delete = {}
        for item in self:
            if mapping_delete.get(item.service_id):
                mapping_delete[item.service_id] = mapping_delete.get(item.service_id) | item
            else:
                mapping_delete[item.service_id] = item
        for service_id, step_ids in mapping_delete.items():
            service_id.message_post(body=_(f"Delete Step: {','.join(step_ids.mapped('description'))}"))
        return super(DPTServiceSteps, self).unlink()


class RequiredField(models.Model):
    _name = 'dpt.service.management.required.fields'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'DPT Service Management required fields'
    _order = 'create_date DESC'

    fields_id = fields.Many2one('ir.model.fields', string='Field', tracking=True)
    field = fields.Selection([
        ('address', 'Address'),
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('distance', 'Distance'),
        ('other', 'Other'),
    ], string='Field Mapping', default='other', tracking=True)
    name = fields.Char(string='Name', tracking=True)
    description = fields.Text(string='Description', tracking=True)
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
        ('selection', 'Selection')
    ], string='Fields type', default='char', tracking=True)
    selection_value_ids = fields.One2many('dpt.sale.order.fields.selection', 'fields_id', string='Selection Value',
                                          tracking=True)
    type = fields.Selection(selection=[
        ("required", "Required"),
        ("options", "Options")
    ], string='Type Fields', default='options', tracking=True)
    service_id = fields.Many2one('dpt.service.management', string='Service', ondelete='cascade', tracking=True)
    using_calculation_price = fields.Boolean('Using Calculation Price', tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Unit', tracking=True)
    default_compute_from = fields.Selection([
        ('weight_in_so', 'Weight in SO'),
        ('volume_in_so', 'Volume in SO'),
        ('packing_num_in_po', 'Packing Num in PO'),
        ('declared_price_in_so', 'Declared Price in SO'),
    ], string='Default From', tracking=True)

    def get_default_value(self, so):
        if self.default_compute_from == 'weight_in_so' and self.fields_type == 'integer':
            return {
                'value_integer': so.weight
            }
        if self.default_compute_from == 'volume_in_so' and self.fields_type == 'integer':
            return {
                'value_integer': so.volume
            }
        if self.default_compute_from == 'packing_num_in_po' and self.fields_type == 'integer':
            return {
                'value_integer': sum(so.purchase_ids.mapped('package_line_ids').mapped('quantity'))
            }
        if self.default_compute_from == 'declared_price_in_so' and self.fields_type == 'integer':
            return {
                'value_integer': sum(so.order_line.mapped('price_declaration'))
            }
        return {}

    def unlink(self):
        # log to front end of deleted bookings
        mapping_delete = {}
        for item in self:
            if mapping_delete.get(item.service_id):
                mapping_delete[item.service_id] = mapping_delete.get(item.service_id) | item
            else:
                mapping_delete[item.service_id] = item
        for service_id, required_field_ids in mapping_delete.items():
            service_id.message_post(
                body=_("Delete Required field: %s") % ','.join(required_field_ids.mapped('uom_id').mapped('name')))
        return super(RequiredField, self).unlink()


class SaleOrderFieldSelection(models.Model):
    _name = 'dpt.sale.order.fields.selection'

    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    name = fields.Char('Selection Value')
