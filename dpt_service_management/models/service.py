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

    parent_id = fields.Many2one('dpt.service.management', string='Parent', index=True, tracking=True)
    child_ids = fields.One2many('dpt.service.management', 'parent_id', string='Childs')
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
    zezo_price = fields.Boolean('Zezo Price', default=False)
    auo_complete = fields.Boolean('Auto Complete', default=False)
    product_id = fields.Many2one('product.product', string='Product')
    # image = fields.Image("Image", required=True, tracking=True)
    visible_to_sale_cs = fields.Boolean('Hiển thị với CS, Sale', default=True,
                                        help='Khi tắt, dịch vụ này chỉ hiển thị cho vận hành và kế toán')
    is_bao_giao = fields.Boolean(default=False, string='Bao giao')
    is_allin = fields.Boolean(default=False, string='All In')

    _sql_constraints = [
        ('code_name_index', 'CREATE INDEX code_name_index ON dpt_service_management (code, name)',
         'Index on code and name'),
        ('code_uniq', 'unique (code)', "Code already exists!")
    ]

    @api.depends('steps_ids')
    def _compute_count_steps(self):
        for rec in self:
            rec.steps_count = len(rec.steps_ids)

    def action_auto_create_product(self):
        service_ids = self.env['dpt.service.management'].search([])
        for service_id in service_ids:
            service_id.action_create_product_id()

    def action_create_product_id(self):
        if not self.product_id:
            product_id = self.env['product.product'].create({
                'name': self.name,
                'type': 'service',
                'uom_id': 1,
                'is_product_service': True,
                'default_code': self.code,
            })
            self.product_id = product_id
        else:
            self.product_id.write({
                'name': self.name,
                'default_code': self.code,
            })

    def write(self, vals):
        res = super(DPTService, self).write(vals)
        for item in self:
            if 'name' in vals:
                item.action_create_product_id()
        return res

    @api.model
    def create(self, vals):
        if vals.get('code', 'NEW') == 'NEW':
            vals['code'] = self._generate_service_code()
        rec = super(DPTService, self).create(vals)
        rec.action_create_product_id()
        return rec

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
            service_id.message_post(body=_(f"Delete Step: {','.join([x.description or '' for x in step_ids])}"))
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
    combo_id = fields.Many2one('dpt.service.combo', string='Combo', ondelete='cascade', tracking=True)
    using_calculation_price = fields.Boolean('Using Calculation Price', tracking=True)

    # Trường đơn vị tính cũ (giữ lại để tương thích ngược)
    uom_id = fields.Many2one('uom.uom', 'Đơn vị tính đơn', tracking=True,
                             help='Đơn vị tính cũ (đã được thay thế bằng condition_uom_ids và pricing_uom_ids)')
    uom_ids = fields.Many2many('uom.uom', string='Đơn vị tính',
                               relation='dpt_required_fields_uom_rel',
                               column1='required_field_id', column2='uom_id',
                               tracking=True,
                               help='Đơn vị tính cũ (đã được thay thế bằng condition_uom_ids và pricing_uom_ids)')

    # Trường đơn vị tính mới (phân biệt mục đích)
    condition_uom_ids = fields.Many2many('uom.uom', string='Đơn vị điều kiện',
                                         relation='dpt_required_fields_condition_uom_rel',
                                         column1='required_field_id', column2='uom_id',
                                         tracking=True,
                                         help='Đơn vị tính dùng làm điều kiện trong dịch vụ')

    pricing_uom_ids = fields.Many2many('uom.uom', string='Đơn vị tính giá',
                                       relation='dpt_required_fields_pricing_uom_rel',
                                       column1='required_field_id', column2='uom_id',
                                       tracking=True,
                                       help='Đơn vị tính dùng để tính giá dịch vụ')

    default_compute_from = fields.Selection([
        ('weight_in_so', 'Weight in SO'),
        ('volume_in_so', 'Volume in SO'),
        ('packing_num_in_po', 'Packing Num in PO'),
        ('declared_price_in_so', 'Declared Price in SO'),
    ], string='Default From', tracking=True)
    code = fields.Char(string='Mã')
    is_template = fields.Boolean(string='Sử dụng lại')

    @api.onchange('uom_id', 'uom_ids')
    def _onchange_legacy_uom_fields(self):
        """Đồng bộ dữ liệu từ các trường đơn vị tính cũ sang trường mới khi có sự thay đổi"""
        if self.uom_id and not self.condition_uom_ids and not self.pricing_uom_ids:
            # Nếu chỉ có uom_id và các trường mới chưa được thiết lập, đồng bộ dữ liệu
            self.condition_uom_ids = [(4, self.uom_id.id)]
            if self.using_calculation_price:
                self.pricing_uom_ids = [(4, self.uom_id.id)]

        if self.uom_ids and not self.condition_uom_ids and not self.pricing_uom_ids:
            # Nếu chỉ có uom_ids và các trường mới chưa được thiết lập, đồng bộ dữ liệu
            self.condition_uom_ids = [(6, 0, self.uom_ids.ids)]
            if self.using_calculation_price:
                self.pricing_uom_ids = [(6, 0, self.uom_ids.ids)]

    def get_default_value(self, so):
        if not so:
            return {}
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
                'value_integer': sum(so.order_line.mapped('declared_unit_price'))
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
            if service_id:
                # Lấy tên đơn vị từ cả các trường đơn vị tính
                uom_names = []
                for field in required_field_ids:
                    if field.uom_id:
                        uom_names.append(field.uom_id.name)
                    if field.uom_ids:
                        uom_names.extend(field.uom_ids.mapped('name'))
                    if field.condition_uom_ids:
                        uom_names.extend(field.condition_uom_ids.mapped('name'))
                    if field.pricing_uom_ids:
                        uom_names.extend(field.pricing_uom_ids.mapped('name'))
                service_id.message_post(
                    body=_("Delete Required field: %s") % ','.join(set(uom_names)))
        return super(RequiredField, self).unlink()


class SaleOrderFieldSelection(models.Model):
    _name = 'dpt.sale.order.fields.selection'

    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    name = fields.Char('Selection Value')
