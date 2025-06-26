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
        # Xác định các thay đổi có liên quan đến giá trị
        value_changes = {}
        for field in ['value_char', 'value_integer', 'value_date', 'selection_value_id']:
            if field in vals:
                old_value = None
                if field == 'selection_value_id':
                    if self.selection_value_id:
                        old_value = self.selection_value_id.name
                    selection = self.env['dpt.sale.order.fields.selection'].browse(vals[field]) if vals[field] else None
                    value_changes[field] = (old_value, selection.name if selection else None)
                else:
                    old_value = getattr(self, field)
                    value_changes[field] = (old_value, vals[field])
        
        # Thực hiện cập nhật dữ liệu
        res = super(SaleOrderField, self).write(vals)
        
        # Kiểm tra trường bắt buộc sau khi ghi
        if 'value_char' in vals or 'value_integer' in vals or 'value_date' in vals:
            self.check_required_fields()
            
        # Cập nhật sale_service_id_key
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
        
        # Ghi log thay đổi nếu có
        if value_changes and self.sale_id:
            message_parts = []
            for field, (old_val, new_val) in value_changes.items():
                if old_val != new_val:
                    field_display = self.fields_id.name or self.fields_id.display_name or "Trường dữ liệu"
                    if field == 'value_char':
                        message_parts.append(_("- %s: '%s' → '%s'") % (field_display, old_val or '', new_val or ''))
                    elif field == 'value_integer':
                        message_parts.append(_("- %s: %s → %s") % (field_display, old_val or '0', new_val or '0'))
                    elif field == 'value_date':
                        old_date = old_val.strftime('%d/%m/%Y') if old_val else ''
                        new_date = new_val.strftime('%d/%m/%Y') if isinstance(new_val, datetime) else new_val or ''
                        message_parts.append(_("- %s: %s → %s") % (field_display, old_date, new_date))
                    elif field == 'selection_value_id':
                        message_parts.append(_("- %s: '%s' → '%s'") % (field_display, old_val or '', new_val or ''))
            
            if message_parts:
                header = _("<strong>Cập nhật thông tin bổ sung</strong>")
                message = header + "<br/>" + "<br/>".join(message_parts)
                # if self.sale_id:
                #     self.sale_id.message_post(body=message)
                
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
        
        # Ghi log khi tạo trường mới có giá trị
        if res.sale_id and res.fields_id:
            has_value = False
            message_parts = []
            field_display = res.fields_id.name or res.fields_id.display_name or "Trường dữ liệu"
            
            if res.fields_type == 'char' and res.value_char:
                message_parts.append(_("- %s: '%s'") % (field_display, res.value_char))
                has_value = True
            elif res.fields_type == 'integer' and res.value_integer:
                message_parts.append(_("- %s: %s") % (field_display, res.value_integer))
                has_value = True
            elif res.fields_type == 'date' and res.value_date:
                date_str = res.value_date.strftime('%d/%m/%Y') if res.value_date else ''
                message_parts.append(_("- %s: %s") % (field_display, date_str))
                has_value = True
            elif res.fields_type == 'selection' and res.selection_value_id:
                message_parts.append(_("- %s: '%s'") % (field_display, res.selection_value_id.name))
                has_value = True
            
            if has_value:
                header = _("<strong>Thêm thông tin bổ sung</strong>")
                message = header + "<br/>" + "<br/>".join(message_parts)
                res.sale_id.message_post(body=message)
                
        return res

    @api.depends('fields_id', 'fields_id.type')
    def _compute_sequence(self):
        for r in self:
            if r.type == 'required':
                r.sequence = 1
            else:
                r.sequence = 0
