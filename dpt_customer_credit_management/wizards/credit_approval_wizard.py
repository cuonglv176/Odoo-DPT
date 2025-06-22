from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CreditApprovalWizard(models.TransientModel):
    _name = 'credit.approval.wizard'
    _description = 'Credit Approval Wizard'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )

    current_credit_limit = fields.Monetary(
        string='Current Credit Limit',
        related='partner_id.credit_limit',
        currency_field='currency_id'
    )

    requested_credit_limit = fields.Monetary(
        string='Requested Credit Limit',
        currency_field='currency_id',
        required=True
    )

    reason = fields.Text(
        string='Reason for Request',
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='partner_id.currency_id'
    )

    supporting_documents = fields.Many2many(
        'ir.attachment',
        string='Supporting Documents'
    )

    def action_submit_approval(self):
        """Gửi yêu cầu phê duyệt"""
        approval_category = self.env.ref(
            'dpt_customer_credit_management.approval_category_credit_limit',
            raise_if_not_found=False
        )

        if not approval_category:
            raise UserError(_("Credit approval category not configured."))

        approval_request = self.env['approval.request'].create({
            'name': f"Credit Limit Approval - {self.partner_id.name}",
            'category_id': approval_category.id,
            'partner_id': self.partner_id.id,
            'reason': self.reason,
            'request_amount': self.requested_credit_limit,
        })

        # Tạo credit history
        self.env['credit.history'].create({
            'partner_id': self.partner_id.id,
            'action': 'approval_requested',
            'old_credit_limit': self.current_credit_limit,
            'new_credit_limit': self.requested_credit_limit,
            'user_id': self.env.user.id,
            'notes': f"Approval requested: {self.reason}",
            'approval_request_id': approval_request.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CreditOverrideWizard(models.TransientModel):
    _name = 'credit.override.wizard'
    _description = 'Credit Override Wizard'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )

    order_amount = fields.Monetary(
        string='Order Amount',
        currency_field='currency_id'
    )

    credit_limit = fields.Monetary(
        string='Credit Limit',
        related='partner_id.credit_limit',
        currency_field='currency_id'
    )

    current_debt = fields.Monetary(
        string='Current Debt',
        related='partner_id.current_debt',
        currency_field='currency_id'
    )

    excess_amount = fields.Monetary(
        string='Excess Amount',
        compute='_compute_excess_amount',
        currency_field='currency_id'
    )

    override_reason = fields.Text(
        string='Override Reason',
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='partner_id.currency_id'
    )

    @api.depends('current_debt', 'order_amount', 'credit_limit')
    def _compute_excess_amount(self):
        for wizard in self:
            total_exposure = wizard.current_debt + wizard.order_amount
            wizard.excess_amount = max(0, total_exposure - wizard.credit_limit)

    def action_override_credit(self):
        """Thực hiện override credit limit"""
        if not self.env.user.has_group('dpt_customer_credit_management.group_credit_manager'):
            raise UserError(_("Only Credit Managers can override credit limits."))

        self.sale_order_id.write({
            'credit_override': True,
            'credit_override_reason': self.override_reason,
            'credit_override_user_id': self.env.user.id,
            'credit_check_status': 'passed',
            'credit_check_message': f"Credit override approved by {self.env.user.name}\nReason: {self.override_reason}"
        })

        # Ghi log
        self.env['credit.history'].create({
            'partner_id': self.partner_id.id,
            'action': 'override',
            'old_credit_limit': self.credit_limit,
            'new_credit_limit': self.credit_limit,
            'user_id': self.env.user.id,
            'notes': f"Credit override for SO {self.sale_order_id.name}: {self.override_reason}",
        })

        return {'type': 'ir.actions.act_window_close'}
