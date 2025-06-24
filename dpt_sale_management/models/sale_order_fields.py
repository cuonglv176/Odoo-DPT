from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import xlrd, xlwt
import xlsxwriter
import base64
import io as stringIOModule
from odoo.modules.module import get_module_resource

class SaleOrderField(models.Model):
    _name = 'dpt.sale.order.fields'

    def _default_sequence(self):
        if self.type == 'required':
            return 1
        return 0

    sequence = fields.Integer(default=_default_sequence, compute='_compute_sequence', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    combo_id = fields.Many2one(related='fields_id.combo_id')
    service_id = fields.Many2one(related='fields_id.service_id')
    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    value_char = fields.Char(string='Value Char')
    value_integer = fields.Float(string='Value Integer')
    value_date = fields.Date(string='Value Date')
    selection_value_id = fields.Many2one('dpt.sale.order.fields.selection', string='Selection Value')
    type = fields.Selection(selection=[
        ("required", "Required"),
        ("options", "Options")
    ], string='Type Fields', default='options', related='fields_id.type')
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
        ('selection', 'Selection'),
    ], string='Fields type', default='char', related='fields_id.fields_type')
    using_calculation_price = fields.Boolean(related='fields_id.using_calculation_price')
    uom_id = fields.Many2one(related="fields_id.uom_id")
    sale_service_id = fields.Many2one('dpt.sale.service.management')
    sale_combo_id = fields.Many2one('dpt.sale.service.management')
    sale_service_id_key = fields.Integer(related='sale_service_id.id', store=True)
    sale_combo_id_key = fields.Integer(related='sale_combo_id.id', store=True)

    @api.onchange('sale_service_id')
    def onchange_sale_service_id(self):
        if self.sale_service_id:
            self.sale_service_id_key = self.sale_service_id.id

    @api.onchange('sale_id')
    def onchange_get_data_required_fields(self):
        if self.sale_id.partner_id.service_field_ids:
            if self.fields_id.is_template:
                for partner_service_field_id in self.sale_id.partner_id.service_field_ids:
                    if self.fields_id.code == partner_service_field_id.code:
                        self.value_char = partner_service_field_id.value_char
                        self.value_integer = partner_service_field_id.value_integer
                        self.value_date = partner_service_field_id.value_date
                        self.selection_value_id = partner_service_field_id.selection_value_id.id

    def check_required_fields(self):
        for r in self:
            if r.env.context.get('onchange_sale_service_ids', False):
                continue
            if r.fields_id.type == 'required' and r.value_integer <= 0 and r.fields_type == 'integer':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and r.value_char == '' and r.fields_type == 'char':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and not r.value_date and r.fields_type == 'date':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and not r.selection_value_id and r.fields_type == 'selection':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)

    def write(self, vals):
        res = super(SaleOrderField, self).write(vals)
        if 'value_char' in vals or 'value_integer' in vals or 'value_date' in vals:
            # self.sale_id.action_calculation()
            self.check_required_fields()
        if 'sale_service_id' in vals and vals.get('sale_service_id'):
            for record in self:
                if record.sale_service_id:
                    record.sale_service_id_key = record.sale_service_id.id
        
        # Cập nhật luồng thanh toán khi thay đổi giá trị selection trong trường là luồng thanh toán
        if 'selection_value_id' in vals and self.fields_id.is_payment_flow:
            selection_value = self.env['dpt.sale.order.fields.selection'].browse(vals['selection_value_id'])
            if selection_value:
                # Cập nhật sale.order
                self.sale_id.write({
                    'payment_flow': selection_value.name
                })
                
                # Cập nhật dpt.export.import.line
                export_import_lines = self.env['dpt.export.import.line'].search([('sale_id', '=', self.sale_id.id)])
                if export_import_lines:
                    export_import_lines.write({
                        'payment_flow': selection_value.name
                    })
                    
        return res

    @api.model
    def create(self, vals_list):
        res = super(SaleOrderField, self).create(vals_list)
        res.check_required_fields()
        if isinstance(vals_list, dict) and vals_list.get('sale_service_id'):
            res.sale_service_id_key = res.sale_service_id.id
            
        # Cập nhật luồng thanh toán khi tạo mới với trường là luồng thanh toán
        if res.fields_id.is_payment_flow and res.selection_value_id:
            # Cập nhật sale.order
            res.sale_id.write({
                'payment_flow': res.selection_value_id.name
            })
            
            # Cập nhật dpt.export.import.line
            export_import_lines = res.env['dpt.export.import.line'].search([('sale_id', '=', res.sale_id.id)])
            if export_import_lines:
                export_import_lines.write({
                    'payment_flow': res.selection_value_id.name
                })
                
        return res

    @api.depends('fields_id', 'fields_id.type')
    def _compute_sequence(self):
        for r in self:
            if r.type == 'required':
                r.sequence = 1
            else:
                r.sequence = 0
