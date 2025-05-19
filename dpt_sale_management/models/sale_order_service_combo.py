from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceCombo(models.Model):
    _name = 'dpt.sale.order.service.combo'
    _description = 'Combo dịch vụ'

    combo_id = fields.Many2one('dpt.service.combo', string='Combo')
    code = fields.Char('Mã combo', required=True)
    description = fields.Text('Mô tả')
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong combo',
                                   related='combo_id.service_ids')
    sale_id = fields.Many2one('sale.order', string='Order')
    price = fields.Float('Giá combo', help='Để trống sẽ tính tổng từ các dịch vụ')
    discount_percent = fields.Float('Giảm giá (%)', default=0.0)
    total_price = fields.Float('Tổng giá sau KM', compute='_compute_total_price')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'combo_id', 'Chi tiết dịch vụ')

