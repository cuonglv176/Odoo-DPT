from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Service Discount Fields
    service_discount_policy_ids = fields.Many2many(
        'dpt.service.discount.policy',
        'sale_order_discount_policy_rel',
        'order_id', 'policy_id',
        string='Chính sách chiết khấu áp dụng',
        readonly=True
    )

    total_service_discount = fields.Monetary(
        string='Tổng chiết khấu dịch vụ',
        compute='_compute_service_discount',
        store=True,
        currency_field='currency_id'
    )

    service_discount_approval_required = fields.Boolean(
        string='Yêu cầu phê duyệt chiết khấu',
        compute='_compute_discount_approval_required',
        store=True
    )

    service_discount_approval_id = fields.Many2one(
        'approval.request',
        string='Phê duyệt chiết khấu đơn hàng',
        copy=False
    )

    @api.depends('order_line.service_discount_amount')
    def _compute_service_discount(self):
        for order in self:
            order.total_service_discount = sum(
                order.order_line.mapped('service_discount_amount')
            )

    @api.depends('total_service_discount')
    def _compute_discount_approval_required(self):
        approval_threshold = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'dpt_sale_discount.order_approval_threshold', 5000000
            )
        )

        for order in self:
            order.service_discount_approval_required = (
                    order.total_service_discount > approval_threshold
            )

    def action_apply_service_discounts(self):
        """Apply available service discounts to order lines"""
        self.ensure_one()

        if self.state not in ['draft', 'sent']:
            raise UserError(_('Chỉ có thể áp dụng chiết khấu cho đơn hàng ở trạng thái Nháp hoặc Đã gửi'))

        # Clear existing discounts
        self.order_line.write({
            'service_discount_policy_id': False,
            'service_discount_amount': 0
        })

        applied_policies = self.env['dpt.service.discount.policy']

        for line in self.order_line:
            if line.service_management_id:
                # Apply service discount
                applicable_policies = self._get_applicable_service_policies(line)
                best_policy = self._select_best_policy(applicable_policies, line)

                if best_policy:
                    discount_amount = best_policy.get_applicable_service_discount(
                        line.service_management_id.id,
                        self.partner_id.id,
                        line.product_uom_qty,
                        line.price_subtotal
                    )

                    if discount_amount > 0:
                        line.write({
                            'service_discount_policy_id': best_policy.id,
                            'service_discount_amount': discount_amount
                        })
                        applied_policies |= best_policy

            elif line.service_combo_id:
                # Apply combo discount
                applicable_policies = self._get_applicable_combo_policies(line)
                best_policy = self._select_best_policy(applicable_policies, line)

                if best_policy:
                    discount_amount = best_policy.get_applicable_combo_discount(
                        line.service_combo_id.id,
                        self.partner_id.id,
                        line.product_uom_qty,
                        line.price_subtotal
                    )

                    if discount_amount > 0:
                        line.write({
                            'service_discount_policy_id': best_policy.id,
                            'service_discount_amount': discount_amount
                        })
                        applied_policies |= best_policy

        # Update applied policies
        self.service_discount_policy_ids = applied_policies

        # Check if approval required
        if self.service_discount_approval_required and not self.service_discount_approval_id:
            return self.action_request_discount_approval()

        self.message_post(
            body=_('Đã áp dụng chiết khấu dịch vụ. Tổng chiết khấu: %s') %
                 self.currency_id.format(self.total_service_discount),
            message_type='notification'
        )

        return True

    def _get_applicable_service_policies(self, line):
        """Get applicable service discount policies for a line"""
        domain = [
            ('state', '=', 'approved'),
            ('active', '=', True),
            ('policy_type', 'in', ['service', 'mixed']),
            '|',
            ('service_management_ids', '=', False),
            ('service_management_ids', 'in', [line.service_management_id.id])
        ]

        return self.env['dpt.service.discount.policy'].search(domain)

    def _get_applicable_combo_policies(self, line):
        """Get applicable combo discount policies for a line"""
        domain = [
            ('state', '=', 'approved'),
            ('active', '=', True),
            ('policy_type', 'in', ['combo', 'mixed']),
            '|',
            ('service_combo_ids', '=', False),
            ('service_combo_ids', 'in', [line.service_combo_id.id])
        ]

        return self.env['dpt.service.discount.policy'].search(domain)

    def _select_best_policy(self, policies, line):
        """Select the best discount policy for a line"""
        if not policies:
            return False

        best_policy = False
        best_discount = 0

        for policy in policies:
            if line.service_management_id:
                discount = policy.get_applicable_service_discount(
                    line.service_management_id.id,
                    self.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
                )
            elif line.service_combo_id:
                discount = policy.get_applicable_combo_discount(
                    line.service_combo_id.id,
                    self.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
                )
            else:
                continue

            if discount > best_discount:
                best_discount = discount
                best_policy = policy

        return best_policy

    def action_request_discount_approval(self):
        """Request approval for high-value discounts"""
        self.ensure_one()

        if self.service_discount_approval_id:
            raise UserError(_('Đã có yêu cầu phê duyệt chiết khấu'))

        # Get approval category for order discounts
        approval_category = self.env.ref(
            'dpt_sale_discount.approval_category_order_discount',
            raise_if_not_found=False
        )

        if not approval_category:
            raise UserError(_('Không tìm thấy danh mục phê duyệt chiết khấu đơn hàng'))

        # Prepare approval request
        approval_vals = {
            'name': f"Phê duyệt chiết khấu đơn hàng: {self.name}",
            'category_id': approval_category.id,
            'request_owner_id': self.env.user.id,
            'date_start': fields.Date.today(),
            'description': f"Đơn hàng: {self.name}\nKhách hàng: {self.partner_id.name}\nTổng chiết khấu: {self.currency_id.format(self.total_service_discount)}",
            'amount': self.total_service_discount,
            'reference': self.name,
            'partner_id': self.partner_id.id,
        }

        approval_request = self.env['approval.request'].create(approval_vals)
        self.service_discount_approval_id = approval_request.id

        # Submit for approval
        approval_request.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Yêu cầu phê duyệt chiết khấu'),
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_confirm(self):
        """Override to check discount approval"""
        for order in self:
            if order.service_discount_approval_required:
                if not order.service_discount_approval_id:
                    raise UserError(_('Đơn hàng có chiết khấu cao cần phê duyệt trước khi xác nhận'))

                if order.service_discount_approval_id.request_status != 'approved':
                    raise UserError(_('Chiết khấu đơn hàng chưa được phê duyệt'))

        return super().action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Service Management Integration
    service_management_id = fields.Many2one(
        'dpt.sale.service.management',
        string='Dịch vụ quản lý'
    )

    service_combo_id = fields.Many2one(
        'dpt.sale.order.service.combo',
        string='Combo dịch vụ'
    )

    # Discount Fields
    service_discount_policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách chiết khấu áp dụng'
    )

    service_discount_amount = fields.Monetary(
        string='Số tiền chiết khấu',
        currency_field='currency_id',
        default=0
    )

    service_discount_percentage = fields.Float(
        string='Phần trăm chiết khấu',
        compute='_compute_service_discount_percentage',
        store=True
    )

    price_after_discount = fields.Monetary(
        string='Giá sau chiết khấu',
        compute='_compute_price_after_discount',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('service_discount_amount', 'price_subtotal')
    def _compute_service_discount_percentage(self):
        for line in self:
            if line.price_subtotal:
                line.service_discount_percentage = (
                        line.service_discount_amount / line.price_subtotal * 100
                )
            else:
                line.service_discount_percentage = 0

    @api.depends('price_subtotal', 'service_discount_amount')
    def _compute_price_after_discount(self):
        for line in self:
            line.price_after_discount = line.price_subtotal - line.service_discount_amount

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)

        # Auto-apply discounts if enabled
        for line in lines:
            if line.order_id.state in ['draft', 'sent']:
                line._auto_apply_discount()

        return lines

    def _auto_apply_discount(self):
        """Auto-apply discount if policy allows"""
        self.ensure_one()

        if self.service_discount_policy_id:
            return  # Already has discount

        auto_policies = self.env['dpt.service.discount.policy'].search([
            ('state', '=', 'approved'),
            ('active', '=', True),
            ('auto_apply', '=', True)
        ])

        if self.service_management_id:
            applicable_policies = auto_policies.filtered(
                lambda p: p.policy_type in ['service', 'mixed'] and
                          (not p.service_management_ids or
                           self.service_management_id in p.service_management_ids)
            )
        elif self.service_combo_id:
            applicable_policies = auto_policies.filtered(
                lambda p: p.policy_type in ['combo', 'mixed'] and
                          (not p.service_combo_ids or
                           self.service_combo_id in p.service_combo_ids)
            )
        else:
            return

        best_policy = self.order_id._select_best_policy(applicable_policies, self)

        if best_policy:
            if self.service_management_id:
                discount_amount = best_policy.get_applicable_service_discount(
                    self.service_management_id.id,
                    self.order_id.partner_id.id,
                    self.product_uom_qty,
                    self.price_subtotal
                )
            else:
                discount_amount = best_policy.get_applicable_combo_discount(
                    self.service_combo_id.id,
                    self.order_id.partner_id.id,
                    self.product_uom_qty,
                    self.price_subtotal
                )

            if discount_amount > 0:
                self.write({
                    'service_discount_policy_id': best_policy.id,
                    'service_discount_amount': discount_amount
                })
