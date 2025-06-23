from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ServiceDiscountApplicationWizard(models.TransientModel):
    _name = 'dpt.service.discount.application.wizard'
    _description = 'Service Discount Application Wizard'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Đơn hàng',
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        required=True
    )

    applicable_policy_ids = fields.Many2many(
        'dpt.service.discount.policy',
        string='Chính sách có thể áp dụng',
        compute='_compute_applicable_policies'
    )

    selected_policy_ids = fields.Many2many(
        'dpt.service.discount.policy',
        'wizard_policy_rel',
        'wizard_id', 'policy_id',
        string='Chính sách được chọn'
    )

    service_line_ids = fields.One2many(
        'dpt.service.discount.line.wizard',
        'wizard_id',
        string='Dịch vụ trong đơn hàng'
    )

    total_discount_preview = fields.Monetary(
        string='Tổng chiết khấu dự kiến',
        compute='_compute_discount_preview',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        related='sale_order_id.currency_id'
    )

    @api.depends('sale_order_id', 'partner_id')
    def _compute_applicable_policies(self):
        for wizard in self:
            if wizard.sale_order_id:
                policies = wizard.sale_order_id._get_applicable_service_discount_policies()
                wizard.applicable_policy_ids = policies
            else:
                wizard.applicable_policy_ids = False

    @api.depends('service_line_ids.discount_amount')
    def _compute_discount_preview(self):
        for wizard in self:
            wizard.total_discount_preview = sum(wizard.service_line_ids.mapped('discount_amount'))

    @api.onchange('selected_policy_ids')
    def _onchange_selected_policies(self):
        """Update service lines when policies change"""
        if self.sale_order_id:
            self._update_service_lines()

    def _update_service_lines(self):
        """Update service lines with discount calculations"""
        if not self.sale_order_id:
            return

        # Clear existing lines
        self.service_line_ids = [(5, 0, 0)]

        service_lines = self.sale_order_id.order_line.filtered(
            lambda l: l.product_id.type == 'service'
        )

        line_vals = []
        for line in service_lines:
            # Find best applicable discount
            best_discount = 0
            best_policy = False

            for policy in self.selected_policy_ids:
                discount = policy.get_applicable_discount(
                    line.product_id.id,
                    self.partner_id.id,
                    line.price_subtotal
                )
                if discount > best_discount:
                    best_discount = discount
                    best_policy = policy

            line_vals.append((0, 0, {
                'sale_line_id': line.id,
                'service_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'original_price': line.price_unit,
                'discount_amount': best_discount,
                'applicable_policy_id': best_policy.id if best_policy else False
            }))

        self.service_line_ids = line_vals

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if 'sale_order_id' in res:
            order = self.env['sale.order'].browse(res['sale_order_id'])
            if order:
                res['partner_id'] = order.partner_id.id

        return res

    def action_apply_discounts(self):
        """Apply selected discounts to sale order"""
        self.ensure_one()

        if not self.selected_policy_ids:
            raise UserError(_('Vui lòng chọn ít nhất một chính sách chiết khấu'))

        order = self.sale_order_id
        applied_policies = []

        for service_line in self.service_line_ids.filtered('applicable_policy_id'):
            sale_line = service_line.sale_line_id
            policy = service_line.applicable_policy_id

            # Find specific policy line for this service
            policy_line = policy.policy_line_ids.filtered(
                lambda l: l.service_id == service_line.service_id
            )

            if not policy_line:
                # Create general policy line if not exists
                policy_line = self.env['dpt.service.discount.policy.line'].create({
                    'policy_id': policy.id,
                    'service_id': service_line.service_id.id,
                    'discount_type': policy.discount_type,
                    'discount_value': policy.discount_value
                })

            # Apply discount to sale line
            if sale_line.apply_service_discount_policy(policy_line[0]):
                if policy not in applied_policies:
                    applied_policies.append(policy)

        # Update order with applied policies
        order.service_discount_policy_ids = [(6, 0, [p.id for p in applied_policies])]

        # Log message
        policy_names = ', '.join(applied_policies.mapped('name'))
        order.message_post(
            body=_('Đã áp dụng chính sách chiết khấu dịch vụ: %s') % policy_names,
            subtype_xmlid='mail.mt_comment'
        )

        return {'type': 'ir.actions.act_window_close'}

    def action_preview_discounts(self):
        """Preview discounts without applying"""
        self._update_service_lines()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Xem trước chiết khấu'),
            'res_model': 'dpt.service.discount.application.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new'
        }


class ServiceDiscountLineWizard(models.TransientModel):
    _name = 'dpt.service.discount.line.wizard'
    _description = 'Service Discount Line Wizard'

    wizard_id = fields.Many2one(
        'dpt.service.discount.application.wizard',
        required=True,
        ondelete='cascade'
    )

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Dòng đơn hàng',
        required=True
    )

    service_id = fields.Many2one(
        'product.product',
        string='Dịch vụ',
        required=True
    )

    quantity = fields.Float(
        string='Số lượng',
        required=True
    )

    original_price = fields.Float(
        string='Đơn giá gốc',
        required=True
    )

    discount_amount = fields.Monetary(
        string='Số tiền chiết khấu',
        currency_field='currency_id'
    )

    final_price = fields.Float(
        string='Đơn giá sau chiết khấu',
        compute='_compute_final_price'
    )

    applicable_policy_id = fields.Many2one(
        'dpt.service.discount.policy',
        string='Chính sách áp dụng'
    )

    currency_id = fields.Many2one(
        related='wizard_id.currency_id'
    )

    @api.depends('original_price', 'discount_amount', 'quantity')
    def _compute_final_price(self):
        for line in self:
            if line.quantity:
                discount_per_unit = line.discount_amount / line.quantity
                line.final_price = line.original_price - discount_per_unit
            else:
                line.final_price = line.original_price
