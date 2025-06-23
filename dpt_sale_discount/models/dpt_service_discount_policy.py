from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class DptServiceDiscountPolicy(models.Model):
    _name = 'dpt.service.discount.policy'
    _description = 'DPT Service Discount Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(
        string='Tên chính sách chiết khấu',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Mã chính sách',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True
    )

    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}"

    # Policy Configuration
    policy_type = fields.Selection([
        ('service', 'Dịch vụ đơn lẻ'),
        ('combo', 'Combo dịch vụ'),
        ('mixed', 'Hỗn hợp')
    ], string='Loại chính sách', default='service', required=True, tracking=True)

    priority = fields.Integer(
        string='Độ ưu tiên',
        default=10,
        help="Số càng cao, độ ưu tiên càng cao"
    )

    # State Management
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi phê duyệt'),
        ('approved', 'Hoạt động'),
        ('paused', 'Tạm dừng'),
        ('expired', 'Hết hạn'),
        ('cancelled', 'Hủy'),
        ('rejected', 'Từ chối')
    ], default='draft', string='Trạng thái', tracking=True, required=True)

    # Approval Integration
    approval_request_id = fields.Many2one(
        'approval.request',
        string='Yêu cầu phê duyệt',
        readonly=True,
        copy=False
    )

    approval_state = fields.Selection(
        related='approval_request_id.request_status',
        string='Trạng thái phê duyệt',
        readonly=True
    )

    # Service Management Integration
    service_management_ids = fields.Many2many(
        'dpt.sale.service.management',
        'discount_policy_service_mgmt_rel',
        'policy_id', 'service_mgmt_id',
        string='Dịch vụ quản lý áp dụng'
    )

    service_combo_ids = fields.Many2many(
        'dpt.sale.order.service.combo',
        'discount_policy_combo_rel',
        'policy_id', 'combo_id',
        string='Combo dịch vụ áp dụng'
    )

    # Customer Targeting
    partner_ids = fields.Many2many(
        'res.partner',
        'discount_policy_partner_rel',
        'policy_id', 'partner_id',
        string='Khách hàng áp dụng',
        domain=[('is_company', '=', True)]
    )

    partner_category_ids = fields.Many2many(
        'res.partner.category',
        'discount_policy_partner_category_rel',
        'policy_id', 'category_id',
        string='Nhóm khách hàng'
    )

    # Time Validity
    date_start = fields.Datetime(
        string='Ngày bắt đầu',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )

    date_end = fields.Datetime(
        string='Ngày kết thúc',
        tracking=True
    )

    is_permanent = fields.Boolean(
        string='Vĩnh viễn',
        default=False,
        help="Chính sách không có thời hạn kết thúc"
    )

    # Discount Configuration
    discount_type = fields.Selection([
        ('percentage', 'Phần trăm (%)'),
        ('fixed_amount', 'Số tiền cố định'),
        ('tiered', 'Bậc thang theo số lượng'),
        ('volume', 'Chiết khấu theo khối lượng')
    ], string='Loại chiết khấu', default='percentage', required=True)

    discount_value = fields.Float(
        string='Giá trị chiết khấu',
        help="Giá trị % hoặc số tiền cố định"
    )

    max_discount_amount = fields.Monetary(
        string='Giới hạn chiết khấu tối đa',
        currency_field='currency_id',
        help="Số tiền chiết khấu tối đa cho mỗi đơn hàng"
    )

    min_order_amount = fields.Monetary(
        string='Giá trị đơn hàng tối thiểu',
        currency_field='currency_id',
        help="Giá trị đơn hàng tối thiểu để áp dụng chiết khấu"
    )

    min_service_quantity = fields.Float(
        string='Số lượng dịch vụ tối thiểu',
        default=1.0,
        help="Số lượng dịch vụ tối thiểu để áp dụng chiết khấu"
    )

    # Tiered Discount Configuration
    discount_tier_ids = fields.One2many(
        'dpt.service.discount.tier',
        'policy_id',
        string='Bậc thang chiết khấu'
    )

    # Service-specific Lines
    service_line_ids = fields.One2many(
        'dpt.service.discount.policy.line',
        'policy_id',
        string='Chi tiết chiết khấu theo dịch vụ'
    )

    # Combo-specific Lines
    combo_line_ids = fields.One2many(
        'dpt.service.combo.discount.line',
        'policy_id',
        string='Chi tiết chiết khấu combo'
    )

    # Usage Statistics
    usage_count = fields.Integer(
        string='Số lần sử dụng',
        compute='_compute_usage_statistics',
        store=True
    )

    total_discount_amount = fields.Monetary(
        string='Tổng tiền chiết khấu đã áp dụng',
        compute='_compute_usage_statistics',
        currency_field='currency_id',
        store=True
    )

    last_used_date = fields.Datetime(
        string='Lần sử dụng cuối',
        compute='_compute_usage_statistics',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Additional Fields
    description = fields.Text(
        string='Mô tả chính sách'
    )

    internal_notes = fields.Text(
        string='Ghi chú nội bộ'
    )

    active = fields.Boolean(
        string='Hoạt động',
        default=True
    )

    # Auto-apply Configuration
    auto_apply = fields.Boolean(
        string='Tự động áp dụng',
        default=False,
        help="Tự động áp dụng chiết khấu khi đủ điều kiện"
    )

    require_approval_amount = fields.Monetary(
        string='Ngưỡng yêu cầu phê duyệt',
        currency_field='currency_id',
        help="Số tiền chiết khấu cần phê duyệt đặc biệt"
    )

    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('dpt.service.discount.policy') or _('New')
        return super().create(vals)

    @api.depends('service_line_ids.usage_count', 'combo_line_ids.usage_count')
    def _compute_usage_statistics(self):
        for record in self:
            service_usage = sum(record.service_line_ids.mapped('usage_count'))
            combo_usage = sum(record.combo_line_ids.mapped('usage_count'))

            record.usage_count = service_usage + combo_usage

            service_amount = sum(record.service_line_ids.mapped('total_discount_amount'))
            combo_amount = sum(record.combo_line_ids.mapped('total_discount_amount'))

            record.total_discount_amount = service_amount + combo_amount

            # Get last used date
            service_dates = record.service_line_ids.mapped('last_used_date')
            combo_dates = record.combo_line_ids.mapped('last_used_date')
            all_dates = [d for d in service_dates + combo_dates if d]

            record.last_used_date = max(all_dates) if all_dates else False

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if not record.is_permanent and record.date_end and record.date_start >= record.date_end:
                raise ValidationError(_('Ngày kết thúc phải sau ngày bắt đầu'))

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for record in self:
            if record.discount_type == 'percentage' and record.discount_value:
                if record.discount_value < 0 or record.discount_value > 100:
                    raise ValidationError(_('Phần trăm chiết khấu phải từ 0 đến 100'))
            elif record.discount_type == 'fixed_amount' and record.discount_value:
                if record.discount_value < 0:
                    raise ValidationError(_('Số tiền chiết khấu phải lớn hơn 0'))

    def action_submit_for_approval(self):
        """Submit policy for approval using Odoo approval system"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Chỉ có thể gửi phê duyệt chính sách ở trạng thái Nháp'))

            if record.approval_request_id:
                raise UserError(_('Chính sách đã có yêu cầu phê duyệt'))

            # Determine approval category
            approval_category = record._get_approval_category()

            # Prepare approval request data
            approval_vals = record._prepare_approval_request_vals(approval_category)

            # Create approval request
            approval_request = self.env['approval.request'].create(approval_vals)

            record.write({
                'approval_request_id': approval_request.id,
                'state': 'submitted'
            })

            # Submit the approval request
            approval_request.action_confirm()

            record.message_post(
                body=_('Đã gửi yêu cầu phê duyệt chính sách chiết khấu'),
                message_type='notification'
            )

    def _get_approval_category(self):
        """Determine which approval category to use"""
        self.ensure_one()

        if self._requires_ceo_approval():
            return self.env.ref('dpt_sale_discount.approval_category_service_discount_ceo')
        elif self.policy_type == 'combo':
            return self.env.ref('dpt_sale_discount.approval_category_combo_discount')
        else:
            return self.env.ref('dpt_sale_discount.approval_category_service_discount_manager')

    def _requires_ceo_approval(self):
        """Check if policy requires CEO approval"""
        self.ensure_one()

        # CEO approval required for:
        # 1. High discount percentage (>20%)
        # 2. High discount amount (>10M VND equivalent)
        # 3. Permanent policies
        # 4. Policies affecting all customers

        ceo_approval_threshold = 20.0  # 20%
        ceo_amount_threshold = 10000000  # 10M VND

        if self.is_permanent:
            return True

        if not self.partner_ids and not self.partner_category_ids:
            return True

        if self.discount_type == 'percentage' and self.discount_value > ceo_approval_threshold:
            return True

        if self.max_discount_amount and self.max_discount_amount > ceo_amount_threshold:
            return True

        return False

    def _prepare_approval_request_vals(self, approval_category):
        """Prepare values for approval request"""
        self.ensure_one()

        # Calculate total potential discount amount
        total_amount = self.max_discount_amount or (
            self.min_order_amount * self.discount_value / 100
            if self.discount_type == 'percentage'
            else self.discount_value
        )

        # Prepare description
        description_lines = [
            f"Chính sách: {self.name}",
            f"Loại: {dict(self._fields['policy_type'].selection)[self.policy_type]}",
            f"Chiết khấu: {self.discount_value}{'%' if self.discount_type == 'percentage' else ' VND'}",
        ]

        if self.service_management_ids:
            service_names = ', '.join(self.service_management_ids.mapped('name'))
            description_lines.append(f"Dịch vụ: {service_names}")

        if self.service_combo_ids:
            combo_names = ', '.join(self.service_combo_ids.mapped('name'))
            description_lines.append(f"Combo: {combo_names}")

        if self.partner_ids:
            partner_names = ', '.join(self.partner_ids.mapped('name'))
            description_lines.append(f"Khách hàng: {partner_names}")

        return {
            'name': f"Phê duyệt chính sách chiết khấu: {self.name}",
            'category_id': approval_category.id,
            'request_owner_id': self.env.user.id,
            'date_start': self.date_start.date() if self.date_start else fields.Date.today(),
            'date_end': self.date_end.date() if self.date_end else None,
            'description': '\n'.join(description_lines),
            'reason': self.description or '',
            'amount': total_amount,
            'quantity': len(self.service_management_ids) + len(self.service_combo_ids),
            'reference': self.code,
            'partner_id': self.partner_ids[0].id if len(self.partner_ids) == 1 else False,
        }

    def action_view_approval_request(self):
        """View the related approval request"""
        self.ensure_one()
        if not self.approval_request_id:
            raise UserError(_('Không có yêu cầu phê duyệt nào'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Yêu cầu phê duyệt'),
            'res_model': 'approval.request',
            'res_id': self.approval_request_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _check_approval_status(self):
        """Cron job to check and update approval status"""
        policies = self.search([
            ('state', '=', 'submitted'),
            ('approval_request_id', '!=', False)
        ])

        for policy in policies:
            approval = policy.approval_request_id

            if approval.request_status == 'approved':
                policy.write({'state': 'approved'})
                policy.message_post(
                    body=_('Chính sách chiết khấu đã được phê duyệt'),
                    message_type='notification'
                )
            elif approval.request_status == 'refused':
                policy.write({'state': 'rejected'})
                policy.message_post(
                    body=_('Chính sách chiết khấu đã bị từ chối'),
                    message_type='notification'
                )
            elif approval.request_status == 'cancel':
                policy.write({'state': 'cancelled'})

    def action_cancel_approval(self):
        """Cancel approval request"""
        for record in self:
            if record.approval_request_id and record.approval_request_id.request_status in ['new', 'pending']:
                record.approval_request_id.action_cancel()
                record.write({'state': 'draft'})
                record.message_post(
                    body=_('Đã hủy yêu cầu phê duyệt'),
                    message_type='notification'
                )

    def action_pause(self):
        """Pause active policy"""
        for record in self:
            if record.state == 'approved':
                record.write({'state': 'paused'})
                record.message_post(
                    body=_('Chính sách đã được tạm dừng'),
                    message_type='notification'
                )

    def action_resume(self):
        """Resume paused policy"""
        for record in self:
            if record.state == 'paused':
                record.write({'state': 'approved'})
                record.message_post(
                    body=_('Chính sách đã được kích hoạt lại'),
                    message_type='notification'
                )

    def _is_policy_applicable(self, partner_id, order_amount=0):
        """Check if policy is applicable for given conditions"""
        self.ensure_one()

        # Check state
        if self.state != 'approved':
            return False

        # Check active
        if not self.active:
            return False

        # Check date validity
        now = fields.Datetime.now()
        if self.date_start and now < self.date_start:
            return False

        if not self.is_permanent and self.date_end and now > self.date_end:
            return False

        # Check minimum order amount
        if self.min_order_amount and order_amount < self.min_order_amount:
            return False

        # Check partner applicability
        if self.partner_ids:
            if partner_id not in self.partner_ids.ids:
                return False

        if self.partner_category_ids:
            partner = self.env['res.partner'].browse(partner_id)
            if not any(cat in partner.category_id.ids for cat in self.partner_category_ids.ids):
                return False

        return True

    def get_applicable_service_discount(self, service_mgmt_id, partner_id, quantity=1, order_amount=0):
        """Get applicable discount for a service management"""
        self.ensure_one()

        if not self._is_policy_applicable(partner_id, order_amount):
            return 0

        # Check service management applicability
        if self.service_management_ids and service_mgmt_id not in self.service_management_ids.ids:
            return 0

        # Check quantity requirement
        if quantity < self.min_service_quantity:
            return 0

        # Get specific service line discount
        service_line = self.service_line_ids.filtered(
            lambda l: l.service_management_id.id == service_mgmt_id
        )

        if service_line:
            return service_line[0].get_discount_amount(quantity, order_amount)

        # Use general policy discount
        return self._calculate_discount_amount(quantity, order_amount)

    def get_applicable_combo_discount(self, combo_id, partner_id, quantity=1, order_amount=0):
        """Get applicable discount for a service combo"""
        self.ensure_one()

        if not self._is_policy_applicable(partner_id, order_amount):
            return 0

        # Check combo applicability
        if self.service_combo_ids and combo_id not in self.service_combo_ids.ids:
            return 0

        # Check quantity requirement
        if quantity < self.min_service_quantity:
            return 0

        # Get specific combo line discount
        combo_line = self.combo_line_ids.filtered(
            lambda l: l.service_combo_id.id == combo_id
        )

        if combo_line:
            return combo_line[0].get_discount_amount(quantity, order_amount)

        # Use general policy discount
        return self._calculate_discount_amount(quantity, order_amount)

    def _calculate_discount_amount(self, quantity, order_amount):
        """Calculate discount amount based on policy configuration"""
        self.ensure_one()

        if self.discount_type == 'percentage':
            discount_amount = order_amount * self.discount_value / 100
        elif self.discount_type == 'fixed_amount':
            discount_amount = self.discount_value * quantity
        elif self.discount_type == 'tiered':
            # Use tiered discount
            applicable_tier = self.discount_tier_ids.filtered(
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
















