from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Credit Management Fields
    credit_limit = fields.Monetary(
        string='Credit Limit',
        currency_field='currency_id',
        help="Maximum credit amount allowed for this customer"
    )

    current_debt = fields.Monetary(
        string='Current Debt',
        currency_field='currency_id',
        compute='_compute_current_debt',
        store=True,
        help="Current outstanding amount"
    )

    available_credit = fields.Monetary(
        string='Available Credit',
        currency_field='currency_id',
        compute='_compute_available_credit',
        help="Remaining credit available"
    )

    credit_status = fields.Selection([
        ('good', 'Good'),
        ('warning', 'Warning'),
        ('blocked', 'Blocked'),
        ('suspended', 'Suspended')
    ], string='Credit Status', default='good', tracking=True)

    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Customer Payment Terms',
        help="Default payment terms for this customer"
    )

    interest_rate = fields.Float(
        string='Interest Rate (%)',
        default=0.0,
        help="Annual interest rate for overdue amounts"
    )

    credit_approval_date = fields.Datetime(
        string='Credit Approval Date',
        tracking=True
    )

    credit_approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True
    )

    credit_notes = fields.Text(
        string='Credit Notes',
        help="Internal notes about customer credit"
    )

    # Computed Fields
    overdue_amount = fields.Monetary(
        string='Overdue Amount',
        currency_field='currency_id',
        compute='_compute_overdue_amount'
    )

    days_overdue = fields.Integer(
        string='Days Overdue',
        compute='_compute_days_overdue'
    )

    credit_utilization = fields.Float(
        string='Credit Utilization (%)',
        compute='_compute_credit_utilization'
    )

    # History
    credit_history_ids = fields.One2many(
        'credit.history',
        'partner_id',
        string='Credit History'
    )

    # Configuration
    block_sales_on_credit_limit = fields.Boolean(
        string='Block Sales on Credit Limit',
        default=True,
        help="Block sales orders when credit limit is exceeded"
    )

    auto_calculate_interest = fields.Boolean(
        string='Auto Calculate Interest',
        default=True,
        help="Automatically calculate interest on overdue amounts"
    )

    @api.depends('debit', 'credit')
    def _compute_current_debt(self):
        for partner in self:
            # Tính tổng công nợ từ account.move.line
            domain = [
                ('partner_id', '=', partner.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('reconciled', '=', False),
                ('parent_state', '=', 'posted')
            ]

            move_lines = self.env['account.move.line'].search(domain)
            partner.current_debt = sum(move_lines.mapped('amount_residual'))

    @api.depends('credit_limit', 'current_debt')
    def _compute_available_credit(self):
        for partner in self:
            partner.available_credit = partner.credit_limit - partner.current_debt

    @api.depends('current_debt', 'credit_limit')
    def _compute_credit_utilization(self):
        for partner in self:
            if partner.credit_limit > 0:
                partner.credit_utilization = (partner.current_debt / partner.credit_limit) * 100
            else:
                partner.credit_utilization = 0.0

    def _compute_overdue_amount(self):
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('reconciled', '=', False),
                ('parent_state', '=', 'posted'),
                ('date_maturity', '<', fields.Date.today())
            ]

            overdue_lines = self.env['account.move.line'].search(domain)
            partner.overdue_amount = sum(overdue_lines.mapped('amount_residual'))

    def _compute_days_overdue(self):
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('reconciled', '=', False),
                ('parent_state', '=', 'posted'),
                ('date_maturity', '<', fields.Date.today())
            ]

            overdue_lines = self.env['account.move.line'].search(domain, order='date_maturity asc', limit=1)
            if overdue_lines:
                overdue_date = overdue_lines[0].date_maturity
                partner.days_overdue = (fields.Date.today() - overdue_date).days
            else:
                partner.days_overdue = 0

    @api.model
    def create(self, vals):
        partner = super().create(vals)
        if 'credit_limit' in vals and vals['credit_limit'] > 0:
            partner._create_credit_history('created', vals['credit_limit'])
        return partner

    def write(self, vals):
        # Ghi lại lịch sử thay đổi credit limit
        if 'credit_limit' in vals:
            for partner in self:
                old_limit = partner.credit_limit
                if old_limit != vals['credit_limit']:
                    partner._create_credit_history('updated', vals['credit_limit'], old_limit)

        result = super().write(vals)

        # Cập nhật credit status
        if 'credit_limit' in vals or 'current_debt' in vals:
            self._update_credit_status()

        return result

    def _create_credit_history(self, action, new_limit, old_limit=0):
        """Tạo bản ghi lịch sử tín dụng"""
        self.env['credit.history'].create({
            'partner_id': self.id,
            'action': action,
            'old_credit_limit': old_limit,
            'new_credit_limit': new_limit,
            'user_id': self.env.user.id,
            'notes': f"Credit limit {action}: {old_limit} → {new_limit}"
        })

    def _update_credit_status(self):
        """Cập nhật trạng thái tín dụng"""
        for partner in self:
            if partner.credit_limit <= 0:
                continue

            utilization = partner.credit_utilization

            if utilization >= 100:
                partner.credit_status = 'blocked'
            elif utilization >= 90:
                partner.credit_status = 'warning'
            elif partner.overdue_amount > 0 and partner.days_overdue > 30:
                partner.credit_status = 'suspended'
            else:
                partner.credit_status = 'good'

    def action_request_credit_approval(self):
        """Tạo yêu cầu phê duyệt tín dụng"""
        approval_category = self.env.ref('dpt_customer_credit_management.approval_category_credit_limit',
                                         raise_if_not_found=False)

        if not approval_category:
            raise UserError(_("Credit approval category not found. Please contact administrator."))

        approval_request = self.env['approval.request'].create({
            'name': f"Credit Limit Approval - {self.name}",
            'category_id': approval_category.id,
            'partner_id': self.id,
            'reason': f"Credit limit approval for customer: {self.name}\nRequested limit: {self.credit_limit}",
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def check_credit_limit(self, amount=0):
        """Kiểm tra hạn mức tín dụng"""
        self.ensure_one()

        if self.credit_limit <= 0:
            return True, ""

        total_exposure = self.current_debt + amount

        if total_exposure > self.credit_limit:
            excess = total_exposure - self.credit_limit
            message = _(
                "Credit limit exceeded!\n"
                "Credit Limit: %s\n"
                "Current Debt: %s\n"
                "Order Amount: %s\n"
                "Total Exposure: %s\n"
                "Excess Amount: %s"
            ) % (
                          self.credit_limit,
                          self.current_debt,
                          amount,
                          total_exposure,
                          excess
                      )
            return False, message

        return True, ""

    @api.model
    def calculate_interest_penalties(self):
        """Tính lãi phạt cho các khoản quá hạn (chạy bằng cron)"""
        partners = self.search([
            ('auto_calculate_interest', '=', True),
            ('interest_rate', '>', 0),
            ('overdue_amount', '>', 0)
        ])

        for partner in partners:
            partner._calculate_partner_interest()

    def _calculate_partner_interest(self):
        """Tính lãi phạt cho một khách hàng"""
        self.ensure_one()

        if self.interest_rate <= 0 or self.overdue_amount <= 0:
            return

        # Tìm các hóa đơn quá hạn
        domain = [
            ('partner_id', '=', self.id),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('reconciled', '=', False),
            ('parent_state', '=', 'posted'),
            ('date_maturity', '<', fields.Date.today())
        ]

        overdue_lines = self.env['account.move.line'].search(domain)

        for line in overdue_lines:
            days_overdue = (fields.Date.today() - line.date_maturity).days
            if days_overdue > 0:
                # Tính lãi phạt
                daily_rate = self.interest_rate / 365 / 100
                interest_amount = line.amount_residual * daily_rate * days_overdue

                if interest_amount > 0:
                    self._create_interest_entry(line, interest_amount, days_overdue)

    def _create_interest_entry(self, original_line, interest_amount, days_overdue):
        """Tạo bút toán lãi phạt"""
        # Tìm hoặc tạo tài khoản lãi phạt
        interest_account = self.env['account.account'].search([
            ('code', '=', '5151'),  # Tài khoản thu lãi phạt
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not interest_account:
            raise UserError(_("Interest income account (5151) not found. Please create it first."))

        # Tạo journal entry cho lãi phạt
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        move_vals = {
            'journal_id': journal.id,
            'date': fields.Date.today(),
            'ref': f"Interest penalty - {self.name} - {days_overdue} days",
            'line_ids': [
                (0, 0, {
                    'account_id': original_line.account_id.id,
                    'partner_id': self.id,
                    'debit': interest_amount,
                    'credit': 0,
                    'name': f"Interest penalty - {days_overdue} days overdue",
                }),
                (0, 0, {
                    'account_id': interest_account.id,
                    'debit': 0,
                    'credit': interest_amount,
                    'name': f"Interest income - {self.name}",
                })
            ]
        }

        move = self.env['account.move'].create(move_vals)
        move.action_post()

        _logger.info(f"Created interest penalty entry for {self.name}: {interest_amount}")
