from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class DptServiceDiscountPolicyLine(models.Model):
    _name = 'dpt.service.discount.policy.line'
    _description = 'Service Discount Policy Line'
    _order = 'policy_id, sequence, service_management_id'

    policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách chiết khấu',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer(
        string='Thứ tự',
        default=10
    )

    service_management_id = fields.Many2one(
        'dpt.sale.service.management',
        string='Dịch vụ quản lý',
        required=True
    )

    # Discount Configuration
    discount_type = fields.Selection([
        ('percentage', 'Phần trăm (%)'),
        ('fixed_amount', 'Số tiền cố định'),
        ('tiered', 'Bậc thang theo số lượng')
    ], string='Loại chiết khấu', default='percentage', required=True)

    discount_value = fields.Float(
        string='Giá trị chiết khấu',
        required=True
    )

    max_discount_amount = fields.Monetary(
        string='Giới hạn chiết khấu tối đa',
        currency_field='currency_id'
    )

    min_quantity = fields.Float(
        string='Số lượng tối thiểu',
        default=1.0
    )

    # Usage Statistics
    usage_count = fields.Integer(
        string='Số lần sử dụng',
        default=0,
        readonly=True
    )

    total_discount_amount = fields.Monetary(
        string='Tổng tiền chiết khấu',
        currency_field='currency_id',
        default=0,
        readonly=True
    )

    last_used_date = fields.Datetime(
        string='Lần sử dụng cuối',
        readonly=True
    )

    currency_id = fields.Many2one(
        related='policy_id.currency_id',
        store=True
    )

    # Tier Configuration for this line
    tier_ids = fields.One2many(
        'dpt.service.discount.line.tier',
        'line_id',
        string='Bậc thang chiết khấu'
    )

    active = fields.Boolean(
        string='Hoạt động',
        default=True
    )

    description = fields.Text(
        string='Mô tả'
    )

    def get_discount_amount(self, quantity, order_amount):
        """Calculate discount amount for this service line"""
        self.ensure_one()

        if quantity < self.min_quantity:
            return 0

        if self.discount_type == 'percentage':
            discount_amount = order_amount * self.discount_value / 100
        elif self.discount_type == 'fixed_amount':
            discount_amount = self.discount_value * quantity
        elif self.discount_type == 'tiered':
            # Use tiered discount for this line
            applicable_tier = self.tier_ids.filtered(
                lambda t: quantity >= t.min_quantity
            ).sorted('min_quantity', reverse=True)

            if applicable_tier:
                tier = applicable_tier[0]
                if tier.discount_type == 'percentage':
                    discount_amount = order_amount * tier.discount_value / 100
                else:
                    discount_amount = tier.discount_value * quantity
            else:
                discount_amount = 0
        else:
            discount_amount = 0

        # Apply maximum discount limit
        if self.max_discount_amount and discount_amount > self.max_discount_amount:
            discount_amount = self.max_discount_amount

        return discount_amount

    def record_usage(self, discount_amount):
        """Record usage of this discount line"""
        self.ensure_one()
        self.write({
            'usage_count': self.usage_count + 1,
            'total_discount_amount': self.total_discount_amount + discount_amount,
            'last_used_date': fields.Datetime.now()
        })