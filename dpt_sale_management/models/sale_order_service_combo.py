from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import xlrd, xlwt
import xlsxwriter
import base64
import io as stringIOModule
from odoo.modules.module import get_module_resource


class ServiceCombo(models.Model):
    _name = 'dpt.service.combo'
    _description = 'Combo dịch vụ'

    name = fields.Char('Tên combo', required=True)
    code = fields.Char('Mã combo', required=True)
    service_template_ids = fields.One2many('dpt.sale.service.management', 'combo_id',
                                           string='Dịch vụ', domain=[('is_template', '=', True)])
    active = fields.Boolean('Hoạt động', default=True)
    description = fields.Text('Mô tả')
    partner_id = fields.Many2one('res.partner', string='Khách hàng',
                                 help='Nếu được chọn, combo này chỉ áp dụng cho khách hàng cụ thể')

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Mã combo phải là duy nhất!"))

    def create_service_template(self, service_id, uom_id, price, qty=1.0):
        """
        Tạo template dịch vụ cho combo
        """
        service = self.env['dpt.service.management'].browse(service_id)
        return self.env['dpt.sale.service.management'].create({
            'service_id': service_id,
            'combo_id': self.id,
            'uom_id': uom_id,
            'price': price,
            'qty': qty,
            'is_template': True,
            'department_id': service.department_id.id,
        })
