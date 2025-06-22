from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ServiceDiscountWizard(models.TransientModel):
    _name = 'service.discount.wizard'
    _description = 'Service Discount Application Wizard'

    order_id = fields.Many2one(
        'sale.order',
        string='Đơn hàng',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )

    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Khách hàng',
        readonly=True
    )

    total_amount = fields.Monetary(
        related='order_id.amount_total',
        string='Tổng tiền đơn hàng',
        readonly=True
    )

    currency_id = fields.Many2one(
        related='order_id.currency_id',
        readonly=True
    )

    available_policy_ids = fields.One2many(
        'service.discount.wizard.policy',
        'wizard_id',
        string='Chính sách có thể áp dụng'
    )

    line_ids = fields.One2many(
        'service.discount.wizard.line',
        'wizard_id',
        string='Chi tiết dòng đơn hàng'
    )

    total_estimated_discount = fields.Monetary(
        string='Tổng chiết khấu ước tính',
        compute='_compute_total_estimated_discount',
        currency_field='currency_id'
    )

    @api.depends('line_ids.discount_amount', 'line_ids.apply_discount')
    def _compute_total_estimated_discount(self):
        for wizard in self:
            wizard.total_estimated_discount = sum(
                line.discount_amount for line in wizard.line_ids
                if line.apply_discount
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if 'order_id' in res:
            order = self.env['sale.order'].browse(res['order_id'])

            # Load available policies
            available_policies = self._get_available_policies(order)
            policy_lines = []

            for policy in available_policies:
                estimated_discount = self._estimate_policy_discount(policy, order)
                policy_lines.append((0, 0, {
                    'policy_id': policy.id,
                    'estimated_discount': estimated_discount,
                    'can_apply': estimated_discount > 0
                }))

            res['available_policy_ids'] = policy_lines

            # Load order lines
            order_lines = []
            for line in order.order_line:
                if line.service_management_id or line.service_combo_id:
                    best_policy = self._get_best_policy_for_line(line, available_policies)
                    discount_amount = 0

                    if best_policy:
                        if line.service_management_id:
                            discount_amount = best_policy.get_applicable_service_discount(
                                line.service_management_id.id,
                                order.partner_id.id,
                                line.product_uom_qty,
                                line.price_subtotal
                            )
                        elif line.service_combo_id:
                            discount_amount = best_policy.get_applicable_combo_discount(
                                line.service_combo_id.id,
                                order.partner_id.id,
                                line.product_uom_qty,
                                line.price_subtotal
                            )

                    order_lines.append((0, 0, {
                        'order_line_id': line.id,
                        'service_management_id': line.service_management_id.id,
                        'service_combo_id': line.service_combo_id.id,
                        'quantity': line.product_uom_qty,
                        'price_subtotal': line.price_subtotal,
                        'selected_policy_id': best_policy.id if best_policy else False,
                        'discount_amount': discount_amount,
                        'apply_discount': discount_amount > 0
                    }))

            res['line_ids'] = order_lines

        return res

    def _get_available_policies(self, order):
        """Get all available discount policies for the order"""
        domain = [
            ('state', '=', 'approved'),
            ('active', '=', True),
            '|',
            ('partner_ids', '=', False),
            ('partner_ids', 'in', [order.partner_id.id])
        ]

        return self.env['dpt.service.discount.policy'].search(domain)

    def _estimate_policy_discount(self, policy, order):
        """Estimate total discount for a policy on the order"""
        total_discount = 0

        for line in order.order_line:
            if line.service_management_id and policy.policy_type in ['service', 'mixed']:
                discount = policy.get_applicable_service_discount(
                    line.service_management_id.id,
                    order.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
                )
                total_discount += discount

            elif line.service_combo_id and policy.policy_type in ['combo', 'mixed']:
                discount = policy.get_applicable_combo_discount(
                    line.service_combo_id.id,
                    order.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
                )
                total_discount += discount

        return total_discount

    def _get_best_policy_for_line(self, line, policies):
        """Get the best policy for a specific order line"""
        best_policy = False
        best_discount = 0

        for policy in policies:
            discount = 0

            if line.service_management_id and policy.policy_type in ['service', 'mixed']:
                discount = policy.get_applicable_service_discount(
                    line.service_management_id.id,
                    line.order_id.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
                )
            elif line.service_combo_id and policy.policy_type in ['combo', 'mixed']:
                discount = policy.get_applicable_combo_discount(
                    line.service_combo_id.id,
                    line.order_id.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
                )

            if discount > best_discount:
                best_discount = discount
                best_policy = policy

        return best_policy

    def action_apply_discounts(self):
        """Apply selected discounts to the order"""
        self.ensure_one()

        if not self.line_ids.filtered('apply_discount'):
            raise UserError(_('Vui lòng chọn ít nhất một dòng để áp dụng chiết khấu'))

        applied_policies = self.env['dpt.service.discount.policy']

        for line in self.line_ids.filtered('apply_discount'):
            if line.selected_policy_id and line.discount_amount > 0:
                # Apply discount to order line
                line.order_line_id.write({
                    'service_discount_policy_id': line.selected_policy_id.id,
                    'service_discount_amount': line.discount_amount
                })

                applied_policies |= line.selected_policy_id

                # Record usage in policy line
                if line.order_line_id.service_management_id:
                    policy_line = line.selected_policy_id.service_line_ids.filtered(
                        lambda l: l.service_management_id == line.order_line_id.service_management_id
                    )
                    if policy_line:
                        policy_line.record_usage(line.discount_amount)

                    elif line.order_line_id.service_combo_id:
                        combo_line = line.selected_policy_id.combo_line_ids.filtered(
                            lambda l: l.service_combo_id == line.order_line_id.service_combo_id
                        )
                        if combo_line:
                            combo_line.record_usage(line.discount_amount)

                        # Update order with applied policies
                    self.order_id.service_discount_policy_ids = applied_policies

                    # Check if approval required
                    if self.order_id.service_discount_approval_required and not self.order_id.service_discount_approval_id:
                        return self.order_id.action_request_discount_approval()

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Thành công'),
                            'message': _('Đã áp dụng chiết khấu cho %d dòng. Tổng chiết khấu: %s') % (
                                len(self.line_ids.filtered('apply_discount')),
                                self.order_id.currency_id.format(self.total_estimated_discount)
                            ),
                            'type': 'success',
                            'sticky': False,
                        }
                    }

class ServiceDiscountWizardPolicy(models.TransientModel):
    _name = 'service.discount.wizard.policy'
    _description = 'Service Discount Wizard Policy Line'

    wizard_id = fields.Many2one(
        'service.discount.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách chiết khấu',
        required=True
    )

    name = fields.Char(
        related='policy_id.name',
        string='Tên chính sách',
        readonly=True
    )

    policy_type = fields.Selection(
        related='policy_id.policy_type',
        readonly=True
    )

    discount_type = fields.Selection(
        related='policy_id.discount_type',
        readonly=True
    )

    discount_value = fields.Float(
        related='policy_id.discount_value',
        readonly=True
    )

    estimated_discount = fields.Monetary(
        string='Chiết khấu ước tính',
        currency_field='currency_id'
    )

    can_apply = fields.Boolean(
        string='Có thể áp dụng',
        default=False
    )

    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
        readonly=True
    )

class ServiceDiscountWizardLine(models.TransientModel):
    _name = 'service.discount.wizard.line'
    _description = 'Service Discount Wizard Line'

    wizard_id = fields.Many2one(
        'service.discount.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Dòng đơn hàng',
        required=True
    )

    service_management_id = fields.Many2one(
        'dpt.sale.service.management',
        string='Dịch vụ quản lý'
    )

    service_combo_id = fields.Many2one(
        'dpt.sale.order.service.combo',
        string='Combo dịch vụ'
    )

    quantity = fields.Float(
        string='Số lượng',
        readonly=True
    )

    price_subtotal = fields.Monetary(
        string='Thành tiền',
        currency_field='currency_id',
        readonly=True
    )

    selected_policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách được chọn',
        domain="[('id', 'in', wizard_id.available_policy_ids.policy_id.ids)]"
    )

    discount_amount = fields.Monetary(
        string='Số tiền chiết khấu',
        currency_field='currency_id',
        compute='_compute_discount_amount',
        store=True
    )

    apply_discount = fields.Boolean(
        string='Áp dụng',
        default=False
    )

    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
        readonly=True
    )

    @api.depends('selected_policy_id', 'quantity', 'price_subtotal')
    def _compute_discount_amount(self):
        for line in self:
            if not line.selected_policy_id:
                line.discount_amount = 0
                continue

            discount = 0

            if line.service_management_id:
                discount = line.selected_policy_id.get_applicable_service_discount(
                    line.service_management_id.id,
                    line.wizard_id.partner_id.id,
                    line.quantity,
                    line.price_subtotal
                )
            elif line.service_combo_id:
                discount = line.selected_policy_id.get_applicable_combo_discount(
                    line.service_combo_id.id,
                    line.wizard_id.partner_id.id,
                    line.quantity,
                    line.price_subtotal
                )

            line.discount_amount = discount
