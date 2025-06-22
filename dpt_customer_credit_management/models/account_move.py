from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """Override để cập nhật credit status sau khi post invoice"""
        result = super().action_post()

        # Cập nhật credit status cho customer invoices
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and move.partner_id:
                move.partner_id._update_credit_status()

        return result


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    days_overdue = fields.Integer(
        string='Days Overdue',
        compute='_compute_days_overdue'
    )

    interest_calculated = fields.Boolean(
        string='Interest Calculated',
        default=False,
        help="Whether interest has been calculated for this overdue amount"
    )

    @api.depends('date_maturity')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for line in self:
            if line.date_maturity and line.date_maturity < today and not line.reconciled:
                line.days_overdue = (today - line.date_maturity).days
            else:
                line.days_overdue = 0
