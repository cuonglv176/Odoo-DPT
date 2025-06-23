from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class DptServiceDiscountTier(models.Model):
    _name = 'dpt.service.discount.tier'
    _description = 'Service Discount Tier'
    _order = 'policy_id, min_quantity'

    policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách chiết khấu',
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
        string='Số lượng tối đa',
        help="Để trống nếu không giới hạn"
    )

    discount_type = fields.Selection([
        ('percentage', 'Phần trăm (%)'),
        ('fixed_amount', 'Số tiền cố định')
    ], string='Loại chiết khấu', default='percentage', required=True)

    discount_value = fields.Float(
        string='Giá trị chiết khấu',
        required=True
    )

    description = fields.Text(
        string='Mô tả'
    )

    @api.constrains('min_quantity', 'max_quantity')
    def _check_quantities(self):
        for record in self:
            if record.max_quantity and record.min_quantity >= record.max_quantity:
                raise ValidationError(_('Số lượng tối đa phải lớn hơn số lượng tối thiểu'))