from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ComboDiscountWizard(models.TransientModel):
    _name = 'combo.discount.wizard'
    _description = 'Combo Discount Application Wizard'

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

    combo_line_ids = fields.One2many(
        'combo.discount.wizard.line',
        'wizard_id',
        string='Combo dịch vụ trong đơn hàng'
    )

    available_combo_policy_ids = fields.One2many(
        'combo.discount.wizard.policy',
        'wizard_id',
        string='Chính sách combo có thể áp dụng'
    )

    total_combo_discount = fields.Monetary(
        string='Tổng chiết khấu combo',
        compute='_compute_total_combo_discount',
        currency_field='currency_id'
    )

    combo_count = fields.Integer(
        string='Số combo',
        compute='_compute_combo_stats'
    )

    eligible_combo_count = fields.Integer(
        string='Số combo đủ điều kiện',
        compute='_compute_combo_stats'
    )

    @api.depends('combo_line_ids.discount_amount', 'combo_line_ids.apply_discount')
    def _compute_total_combo_discount(self):
        for wizard in self:
            wizard.total_combo_discount = sum(
                line.discount_amount for line in wizard.combo_line_ids
                if line.apply_discount
            )

    @api.depends('combo_line_ids')
    def _compute_combo_stats(self):
        for wizard in self:
            wizard.combo_count = len(wizard.combo_line_ids)
            wizard.eligible_combo_count = len(
                wizard.combo_line_ids.filtered('best_policy_id')
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if 'order_id' in res:
            order = self.env['sale.order'].browse(res['order_id'])

            # Load combo lines from order
            combo_lines = []
            combo_order_lines = order.order_line.filtered('service_combo_id')

            # Get available combo policies
            available_policies = self._get_available_combo_policies(order)
            policy_lines = []

            for policy in available_policies:
                estimated_discount = self._estimate_combo_policy_discount(policy, combo_order_lines)
                policy_lines.append((0, 0, {
                    'policy_id': policy.id,
                    'estimated_total_discount': estimated_discount,
                    'applicable_combo_count': len(self._get_applicable_combos(policy, combo_order_lines))
                }))

            res['available_combo_policy_ids'] = policy_lines

            # Process each combo line
            for line in combo_order_lines:
                best_policy = self._get_best_combo_policy(line, available_policies)
                discount_amount = 0

                if best_policy:
                    discount_amount = best_policy.get_applicable_combo_discount(
                        line.service_combo_id.id,
                        order.partner_id.id,
                        line.product_uom_qty,
                        line.price_subtotal
                    )

                combo_lines.append((0, 0, {
                    'order_line_id': line.id,
                    'service_combo_id': line.service_combo_id.id,
                    'combo_name': line.service_combo_id.name,
                    'quantity': line.product_uom_qty,
                    'unit_price': line.price_unit,
                    'subtotal': line.price_subtotal,
                    'best_policy_id': best_policy.id if best_policy else False,
                    'discount_amount': discount_amount,
                    'apply_discount': discount_amount > 0
                }))

            res['combo_line_ids'] = combo_lines

        return res

    def _get_available_combo_policies(self, order):
        """Get available combo discount policies for the order"""
        domain = [
            ('state', '=', 'approved'),
            ('active', '=', True),
            ('policy_type', 'in', ['combo', 'mixed']),
            '|',
            ('partner_ids', '=', False),
            ('partner_ids', 'in', [order.partner_id.id])
        ]

        return self.env['dpt.service.discount.policy'].search(domain)

    def _estimate_combo_policy_discount(self, policy, combo_lines):
        """Estimate total discount for a combo policy"""
        total_discount = 0

        for line in combo_lines:
            discount = policy.get_applicable_combo_discount(
                line.service_combo_id.id,
                line.order_id.partner_id.id,
                line.product_uom_qty,
                line.price_subtotal
            )
            total_discount += discount

        return total_discount

    def _get_applicable_combos(self, policy, combo_lines):
        """Get combo lines applicable for a policy"""
        applicable = []

        for line in combo_lines:
            if policy.get_applicable_combo_discount(
                    line.service_combo_id.id,
                    line.order_id.partner_id.id,
                    line.product_uom_qty,
                    line.price_subtotal
            ) > 0:
                applicable.append(line)

        return applicable

    def _get_best_combo_policy(self, line, policies):
        """Get the best combo policy for a line"""
        best_policy = False
        best_discount = 0

        for policy in policies:
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

    def action_apply_combo_discounts(self):
        """Apply selected combo discounts"""
        self.ensure_one()

        applied_lines = self.combo_line_ids.filtered('apply_discount')

        if not applied_lines:
            raise UserError(_('Vui lòng chọn ít nhất một combo để áp dụng chiết khấu'))

        applied_policies = self.env['dpt.service.discount.policy']

        for line in applied_lines:
            if line.best_policy_id and line.discount_amount > 0:
                # Apply discount to order line
                line.order_line_id.write({
                    'service_discount_policy_id': line.best_policy_id.id,
                    'service_discount_amount': line.discount_amount
                })

                applied_policies |= line.best_policy_id

                # Record usage in combo policy line
                combo_policy_line = line.best_policy_id.combo_line_ids.filtered(
                    lambda l: l.service_combo_id == line.service_combo_id
                )
                if combo_policy_line:
                    combo_policy_line.record_usage(line.discount_amount)

        # Update order with applied policies
        existing_policies = self.order_id.service_discount_policy_ids
        self.order_id.service_discount_policy_ids = existing_policies | applied_policies

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã áp dụng chiết khấu combo cho %d dòng. Tổng chiết khấu: %s') % (
                    len(applied_lines),
                    self.order_id.currency_id.format(self.total_combo_discount)
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_preview_combo_discounts(self):
        """Preview combo discounts without applying"""
        self.ensure_one()

        preview_data = []
        total_discount = 0

        for line in self.combo_line_ids.filtered('apply_discount'):
            preview_data.append({
                'combo_name': line.combo_name,
                'quantity': line.quantity,
                'subtotal': line.subtotal,
                'policy_name': line.best_policy_id.name if line.best_policy_id else '',
                'discount_amount': line.discount_amount
            })
            total_discount += line.discount_amount

        # Create preview report or return data
        return {
            'type': 'ir.actions.report',
            'report_name': 'dpt_sale_discount.combo_discount_preview_report',
            'report_type': 'qweb-html',
            'data': {
                'preview_data': preview_data,
                'total_discount': total_discount,
                'order_name': self.order_id.name,
                'partner_name': self.partner_id.name
            },
            'context': self.env.context,
        }

    def action_auto_select_best_combos(self):
        """Auto-select best combo discounts"""
        self.ensure_one()

        for line in self.combo_line_ids:
            if line.best_policy_id and line.discount_amount > 0:
                line.apply_discount = True
            else:
                line.apply_discount = False

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã chọn tự động'),
                'message': _('Đã chọn tự động %d combo có chiết khấu tốt nhất') %
                           len(self.combo_line_ids.filtered('apply_discount')),
                'type': 'info',
            }
        }


class ComboDiscountWizardLine(models.TransientModel):
    _name = 'combo.discount.wizard.line'
    _description = 'Combo Discount Wizard Line'

    wizard_id = fields.Many2one(
        'combo.discount.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Dòng đơn hàng',
        required=True
    )

    service_combo_id = fields.Many2one(
        'dpt.sale.order.service.combo',
        string='Combo dịch vụ',
        required=True
    )

    combo_name = fields.Char(
        string='Tên combo',
        readonly=True
    )

    quantity = fields.Float(
        string='Số lượng',
        readonly=True
    )

    unit_price = fields.Monetary(
        string='Đơn giá',
        currency_field='currency_id',
        readonly=True
    )

    subtotal = fields.Monetary(
        string='Thành tiền',
        currency_field='currency_id',
        readonly=True
    )

    best_policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách tốt nhất'
    )

    alternative_policy_ids = fields.Many2many(
        'dpt.service.discount.policy',
        string='Chính sách thay thế',
        compute='_compute_alternative_policies'
    )

    selected_policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách được chọn',
        domain="[('id', 'in', alternative_policy_ids)]"
    )

    discount_amount = fields.Monetary(
        string='Số tiền chiết khấu',
        currency_field='currency_id',
        compute='_compute_discount_amount',
        store=True
    )

    discount_percentage = fields.Float(
        string='Phần trăm chiết khấu',
        compute='_compute_discount_percentage'
    )

    apply_discount = fields.Boolean(
        string='Áp dụng',
        default=False
    )

    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
        readonly=True
    )

    @api.depends('service_combo_id')
    def _compute_alternative_policies(self):
        for line in self:
            if line.service_combo_id:
                # Get all applicable policies for this combo
                policies = line.wizard_id.available_combo_policy_ids.mapped('policy_id')
                applicable = []

                for policy in policies:
                    discount = policy.get_applicable_combo_discount(
                        line.service_combo_id.id,
                        line.wizard_id.partner_id.id,
                        line.quantity,
                        line.subtotal
                    )
                    if discount > 0:
                        applicable.append(policy.id)

                line.alternative_policy_ids = [(6, 0, applicable)]
            else:
                line.alternative_policy_ids = [(6, 0, [])]

            @api.depends('selected_policy_id', 'best_policy_id', 'quantity', 'subtotal')
            def _compute_discount_amount(self):
                for line in self:
                    policy = line.selected_policy_id or line.best_policy_id

                    if policy and line.service_combo_id:
                        line.discount_amount = policy.get_applicable_combo_discount(
                            line.service_combo_id.id,
                            line.wizard_id.partner_id.id,
                            line.quantity,
                            line.subtotal
                        )
                    else:
                        line.discount_amount = 0

            @api.depends('discount_amount', 'subtotal')
            def _compute_discount_percentage(self):
                for line in self:
                    if line.subtotal:
                        line.discount_percentage = (line.discount_amount / line.subtotal) * 100
                    else:
                        line.discount_percentage = 0

class ComboDiscountWizardPolicy(models.TransientModel):
    _name = 'combo.discount.wizard.policy'
    _description = 'Combo Discount Wizard Policy'

    wizard_id = fields.Many2one(
        'combo.discount.wizard',
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

    estimated_total_discount = fields.Monetary(
        string='Tổng chiết khấu ước tính',
        currency_field='currency_id'
    )

    applicable_combo_count = fields.Integer(
        string='Số combo áp dụng được'
    )

    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
        readonly=True
    )

