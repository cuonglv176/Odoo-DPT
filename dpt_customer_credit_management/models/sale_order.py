from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    credit_check_status = fields.Selection([
        ('not_checked', 'Not Checked'),
        ('passed', 'Passed'),
        ('warning', 'Warning'),
        ('blocked', 'Blocked')
    ], string='Credit Check Status', default='not_checked', tracking=True)

    credit_check_message = fields.Text(
        string='Credit Check Message',
        readonly=True
    )

    credit_override = fields.Boolean(
        string='Credit Override',
        help="Override credit limit check for this order"
    )

    credit_override_reason = fields.Text(
        string='Override Reason'
    )

    credit_override_user_id = fields.Many2one(
        'res.users',
        string='Override By'
    )

    @api.onchange('partner_id', 'order_line')
    def _onchange_credit_check(self):
        if self.partner_id and self.amount_total > 0:
            self._check_customer_credit()

    def _check_customer_credit(self):
        """Kiểm tra tín dụng khách hàng"""
        if not self.partner_id or self.credit_override:
            return

        # Kiểm tra hạn mức tín dụng
        credit_ok, message = self.partner_id.check_credit_limit(self.amount_total)

        if not credit_ok:
            self.credit_check_status = 'blocked'
            self.credit_check_message = message

            # Hiển thị cảnh báo
            if self.partner_id.block_sales_on_credit_limit:
                return {
                    'warning': {
                        'title': _('Credit Limit Exceeded'),
                        'message': message + _(
                            '\n\nThis order cannot be confirmed unless credit limit is increased or payment is received.')
                    }
                }
        else:
            # Kiểm tra mức độ sử dụng tín dụng
            utilization = (
                                      self.partner_id.current_debt + self.amount_total) / self.partner_id.credit_limit * 100 if self.partner_id.credit_limit > 0 else 0

            if utilization >= 80:
                self.credit_check_status = 'warning'
                self.credit_check_message = _(
                    "Credit utilization will be %.1f%% after this order.\n"
                    "Please monitor customer payments closely."
                ) % utilization
            else:
                self.credit_check_status = 'passed'
                self.credit_check_message = _("Credit check passed.")

    def action_confirm(self):
        """Override để kiểm tra tín dụng trước khi confirm"""
        for order in self:
            if order.partner_id and not order.credit_override:
                credit_ok, message = order.partner_id.check_credit_limit(order.amount_total)

                if not credit_ok and order.partner_id.block_sales_on_credit_limit:
                    raise UserError(
                        _("Cannot confirm order for %s\n\n%s\n\n"
                          "Please increase credit limit or receive payment before confirming this order.")
                        % (order.partner_id.name, message)
                    )

        return super().action_confirm()

    def action_credit_override(self):
        """Cho phép override credit limit"""
        if not self.env.user.has_group('dpt_customer_credit_management.group_credit_manager'):
            raise UserError(_("Only Credit Managers can override credit limits."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Credit Override'),
            'res_model': 'credit.override.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_order_amount': self.amount_total,
            }
        }
