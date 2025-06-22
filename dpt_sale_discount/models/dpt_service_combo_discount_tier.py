from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class DptServiceComboDiscountTier(models.Model):
    _name = 'dpt.service.combo.discount.tier'
    _description = 'Service Combo Discount Tier'
    _order = 'line_id, min_quantity'

    line_id = fields.Many2one(
        'dpt.service.combo.discount.line',
        string='Dòng chiết khấu combo',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        string='Tên bậc',
        required=True
    )

    min_quantity = fields.Float(
        string='Số lượng tối thiểu',
        required=True,
        default=1.0
    )

    max_quantity = fields.Float(
        string='Số lượng tối đa'
    )

    discount_type = fields.Selection([
        ('percentage', 'Phần trăm (%)'),
        ('fixed_amount', 'Số tiền cố định')
    ], string='Loại chiết khấu', default='percentage', required=True)

    discount_value = fields.Float(
        string='Giá trị chiết khấu',
        required=True
    )
