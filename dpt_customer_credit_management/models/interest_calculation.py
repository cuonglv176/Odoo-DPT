from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import calendar


class InterestCalculation(models.Model):
    _name = 'interest.calculation'
    _description = 'Interest Calculation for Overdue Payments'
    _order = 'calculation_date desc, partner_id'
    _rec_name = 'display_name'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('is_company', '=', True)]
    )

    calculation_date = fields.Date(
        string='Calculation Date',
        default=fields.Date.today,
        required=True
    )

    period_start = fields.Date(
        string='Period Start',
        required=True
    )

    period_end = fields.Date(
        string='Period End',
        required=True
    )

    # Số liệu tự động tính toán từ hệ thống
    opening_balance = fields.Monetary(
        string='Opening Balance',
        currency_field='currency_id',
        compute='_compute_balances',
        store=True,
        help="Giá trị khoản vay đầu kỳ"
    )

    period_increase = fields.Monetary(
        string='Period Increase',
        currency_field='currency_id',
        compute='_compute_balances',
        store=True,
        help="Giá trị phát sinh tăng trong kỳ (hóa đơn mới)"
    )

    payment_amount = fields.Monetary(
        string='Payment Amount',
        currency_field='currency_id',
        compute='_compute_balances',
        store=True,
        help="Số tiền thanh toán trong kỳ"
    )

    outstanding_balance = fields.Monetary(
        string='Outstanding Balance',
        currency_field='currency_id',
        compute='_compute_balances',
        store=True,
        help="Số tiền còn nợ cuối kỳ"
    )

    # Thông tin kỳ hạn
    interest_start_date = fields.Date(
        string='Interest Start Date',
        compute='_compute_interest_dates',
        store=True,
        help="Ngày bắt đầu kỳ tính lãi"
    )

    due_date = fields.Date(
        string='Due Date',
        compute='_compute_interest_dates',
        store=True,
        help="Ngày đến hạn thanh toán"
    )

    payment_date = fields.Date(
        string='Payment Date',
        compute='_compute_interest_dates',
        store=True,
        help="Ngày thanh toán thực tế"
    )

    # Tính toán lãi tự động
    interest_days = fields.Integer(
        string='Interest Days',
        compute='_compute_interest_calculation',
        store=True,
        help="Số ngày tính lãi"
    )

    monthly_interest_rate = fields.Float(
        string='Monthly Interest Rate (%)',
        related='partner_id.interest_rate',
        help="Lãi suất /tháng từ thông tin khách hàng"
    )

    daily_interest_rate = fields.Float(
        string='Daily Interest Rate (%)',
        compute='_compute_interest_calculation',
        store=True,
        help="Lãi suất hàng ngày"
    )

    interest_amount = fields.Monetary(
        string='Interest Amount',
        currency_field='currency_id',
        compute='_compute_interest_calculation',
        store=True,
        help="Tiền lãi trả chậm"
    )

    # Trạng thái
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('posted', 'Posted'),
        ('paid', 'Paid')
    ], string='Status', default='draft', tracking=True)

    # Thông tin bổ sung
    notes = fields.Text(
        string='Notes',
        compute='_compute_notes',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='partner_id.currency_id',
        store=True
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name'
    )

    # Liên kết với bút toán
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True
    )

    # Chi tiết các hóa đơn liên quan
    invoice_line_ids = fields.One2many(
        'interest.calculation.line',
        'calculation_id',
        string='Invoice Lines'
    )

    @api.depends('partner_id', 'period_start', 'period_end')
    def _compute_balances(self):
        """Tính toán số dư đầu kỳ, phát sinh và thanh toán"""
        for record in self:
            if not record.partner_id or not record.period_start or not record.period_end:
                record.opening_balance = 0
                record.period_increase = 0
                record.payment_amount = 0
                record.outstanding_balance = 0
                continue

            # Số dư đầu kỳ (tổng nợ trước ngày bắt đầu kỳ)
            opening_domain = [
                ('partner_id', '=', record.partner_id.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('parent_state', '=', 'posted'),
                ('date', '<', record.period_start)
            ]
            opening_lines = self.env['account.move.line'].search(opening_domain)
            record.opening_balance = sum(opening_lines.mapped('amount_residual'))

            # Phát sinh tăng trong kỳ (hóa đơn bán mới)
            increase_domain = [
                ('partner_id', '=', record.partner_id.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('parent_state', '=', 'posted'),
                ('move_id.move_type', '=', 'out_invoice'),
                ('date', '>=', record.period_start),
                ('date', '<=', record.period_end)
            ]
            increase_lines = self.env['account.move.line'].search(increase_domain)
            record.period_increase = sum(increase_lines.mapped('debit')) - sum(increase_lines.mapped('credit'))

            # Thanh toán trong kỳ
            payment_domain = [
                ('partner_id', '=', record.partner_id.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('parent_state', '=', 'posted'),
                ('move_id.move_type', '=', 'entry'),
                ('date', '>=', record.period_start),
                ('date', '<=', record.period_end),
                ('credit', '>', 0)
            ]
            payment_lines = self.env['account.move.line'].search(payment_domain)
            record.payment_amount = sum(payment_lines.mapped('credit'))

            # Số dư cuối kỳ
            record.outstanding_balance = record.opening_balance + record.period_increase - record.payment_amount

    @api.depends('partner_id', 'period_start', 'period_end')
    def _compute_interest_dates(self):
        """Tính toán các ngày liên quan đến lãi"""
        for record in self:
            if not record.partner_id:
                continue

            # Tìm hóa đơn quá hạn đầu tiên trong kỳ
            overdue_invoices = self.env['account.move'].search([
                ('partner_id', '=', record.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', record.period_end),
                ('amount_residual', '>', 0)
            ], order='invoice_date_due asc', limit=1)

            if overdue_invoices:
                record.interest_start_date = overdue_invoices.invoice_date_due
                record.due_date = overdue_invoices.invoice_date_due

                # Tìm ngày thanh toán gần nhất
                payment_lines = self.env['account.move.line'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('account_id.account_type', '=', 'asset_receivable'),
                    ('parent_state', '=', 'posted'),
                    ('date', '>', overdue_invoices.invoice_date_due),
                    ('credit', '>', 0)
                ], order='date desc', limit=1)

                if payment_lines:
                    record.payment_date = payment_lines.date
                else:
                    record.payment_date = record.period_end
            else:
                record.interest_start_date = record.period_start
                record.due_date = record.period_start
                record.payment_date = record.period_end

    @api.depends('due_date', 'payment_date', 'outstanding_balance', 'monthly_interest_rate')
    def _compute_interest_calculation(self):
        """Tính toán lãi phạt"""
        for record in self:
            # Tính số ngày chậm trả
            if record.due_date and record.payment_date and record.payment_date > record.due_date:
                delta = record.payment_date - record.due_date
                record.interest_days = delta.days
            else:
                record.interest_days = 0

            # Tính lãi suất hàng ngày (1 tháng = 30 ngày)
            if record.monthly_interest_rate:
                record.daily_interest_rate = record.monthly_interest_rate / 30
            else:
                record.daily_interest_rate = 0

            # Tính tiền lãi
            if record.outstanding_balance > 0 and record.interest_days > 0 and record.daily_interest_rate > 0:
                record.interest_amount = record.outstanding_balance * (
                            record.daily_interest_rate / 100) * record.interest_days
            else:
                record.interest_amount = 0

    @api.depends('partner_id', 'period_start', 'period_end', 'interest_days', 'outstanding_balance')
    def _compute_notes(self):
        """Tự động tạo ghi chú"""
        for record in self:
            notes = []

            if record.outstanding_balance > 0:
                notes.append(f"Số dư nợ: {record.outstanding_balance:,.0f}")

            if record.interest_days > 0:
                notes.append(f"Chậm trả {record.interest_days} ngày")

            if record.interest_amount > 0:
                notes.append(f"Lãi phạt: {record.interest_amount:,.0f}")

            # Thêm thông tin về hóa đơn quá hạn
            overdue_invoices = self.env['account.move'].search([
                ('partner_id', '=', record.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', fields.Date.today()),
                ('amount_residual', '>', 0)
            ])

            if overdue_invoices:
                notes.append(f"Có {len(overdue_invoices)} hóa đơn quá hạn")

            record.notes = '; '.join(notes)

    @api.depends('partner_id', 'calculation_date', 'interest_amount')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id:
                record.display_name = f"{record.partner_id.name} - {record.calculation_date} - {record.interest_amount:,.0f}"
            else:
                record.display_name = "New Interest Calculation"

    def action_calculate_interest(self):
        """Tính toán lãi phạt và tạo chi tiết"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft records can be calculated."))

            # Xóa các dòng chi tiết cũ
            record.invoice_line_ids.unlink()

            # Tạo chi tiết cho từng hóa đơn quá hạn
            record._create_invoice_lines()

            record.state = 'calculated'

    def _create_invoice_lines(self):
        """Tạo chi tiết tính lãi cho từng hóa đơn"""
        self.ensure_one()

        # Tìm các hóa đơn quá hạn
        overdue_invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date_due', '<=', self.period_end),
            ('amount_residual', '>', 0)
        ], order='invoice_date_due asc')

        sequence = 10
        for invoice in overdue_invoices:
            # Tính số ngày quá hạn cho hóa đơn này
            if invoice.invoice_date_due < self.period_end:
                overdue_days = (self.period_end - invoice.invoice_date_due).days
            else:
                overdue_days = 0

            if overdue_days > 0:
                # Tính lãi cho hóa đơn này
                daily_rate = self.monthly_interest_rate / 30 if self.monthly_interest_rate else 0
                line_interest = invoice.amount_residual * (daily_rate / 100) * overdue_days

                self.env['interest.calculation.line'].create({
                    'calculation_id': self.id,
                    'sequence': sequence,
                    'invoice_id': invoice.id,
                    'invoice_date': invoice.invoice_date,
                    'due_date': invoice.invoice_date_due,
                    'principal_amount': invoice.amount_residual,
                    'overdue_days': overdue_days,
                    'daily_interest_rate': daily_rate,
                    'interest_amount': line_interest,
                    'description': f"Lãi phạt HĐ {invoice.name} - {overdue_days} ngày"
                })

                sequence += 10

    def action_post_interest(self):
        """Tạo bút toán ghi nhận lãi phạt"""
        for record in self:
            if record.state != 'calculated':
                raise UserError(_("Only calculated records can be posted."))

            if record.interest_amount <= 0:
                raise UserError(_("Interest amount must be greater than zero."))

            # Tạo bút toán
            move = record._create_interest_journal_entry()
            record.move_id = move.id
            record.state = 'posted'

    def _create_interest_journal_entry(self):
        """Tạo bút toán ghi nhận lãi phạt"""
        self.ensure_one()

        # Tìm tài khoản
        receivable_account = self.partner_id.property_account_receivable_id
        interest_account = self._get_interest_income_account()

        # Tìm journal
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not journal:
            raise UserError(_("No general journal found."))

        # Tạo move
        move_vals = {
            'journal_id': journal.id,
            'date': self.calculation_date,
            'ref': f"Interest penalty - {self.partner_id.name} - {self.period_start} to {self.period_end}",
            'line_ids': [
                (0, 0, {
                    'account_id': receivable_account.id,
                    'partner_id': self.partner_id.id,
                    'name': f"Interest penalty - {self.interest_days} days overdue",
                    'debit': self.interest_amount,
                    'credit': 0,
                }),
                (0, 0, {
                    'account_id': interest_account.id,
                    'name': f"Interest income - {self.partner_id.name}",
                    'debit': 0,
                    'credit': self.interest_amount,
                })
            ]
        }

        move = self.env['account.move'].create(move_vals)
        move.action_post()

        return move

    def _get_interest_income_account(self):
        """Lấy tài khoản thu lãi phạt"""
        account = self.env['account.account'].search([
            ('code', '=', '5151'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not account:
            # Tạo tài khoản nếu chưa có
            account = self.env['account.account'].create({
                'name': 'Interest Income - Late Payment',
                'code': '5151',
                'account_type': 'income_other',
                'company_id': self.env.company.id,
            })

        return account

    @api.model
    def auto_create_monthly_calculations(self):
        """Tự động tạo bảng tính lãi hàng tháng"""
        # Lấy tháng trước
        today = fields.Date.today()
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year

        period_start = datetime(last_year, last_month, 1).date()
        period_end = datetime(last_year, last_month, calendar.monthrange(last_year, last_month)[1]).date()

        # Tìm khách hàng có nợ quá hạn
        partners_with_overdue = self.env['res.partner'].search([
            ('is_company', '=', True),
            ('customer_rank', '>', 0),
            ('overdue_amount', '>', 0)
        ])

        created_records = self.env['interest.calculation']

        for partner in partners_with_overdue:
            # Kiểm tra xem đã có bản ghi cho tháng này chưa
            existing = self.search([
                ('partner_id', '=', partner.id),
                ('period_start', '=', period_start),
                ('period_end', '=', period_end)
            ])

            if not existing:
                record = self.create({
                    'partner_id': partner.id,
                    'calculation_date': today,
                    'period_start': period_start,
                    'period_end': period_end,
                })
                created_records |= record

        # Tự động tính toán
        created_records.action_calculate_interest()

        return created_records


class InterestCalculationLine(models.Model):
    _name = 'interest.calculation.line'
    _description = 'Interest Calculation Line Details'
    _order = 'sequence, due_date'

    calculation_id = fields.Many2one(
        'interest.calculation',
        string='Interest Calculation',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer(string='Sequence', default=10)

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        domain=[('move_type', '=', 'out_invoice')]
    )

    invoice_date = fields.Date(
        string='Invoice Date',
        related='invoice_id.invoice_date'
    )

    due_date = fields.Date(
        string='Due Date',
        related='invoice_id.invoice_date_due'
    )

    description = fields.Char(string='Description', required=True)

    principal_amount = fields.Monetary(
        string='Principal Amount',
        currency_field='currency_id',
        help="Số tiền gốc còn nợ"
    )

    overdue_days = fields.Integer(
        string='Overdue Days',
        help="Số ngày quá hạn"
    )

    daily_interest_rate = fields.Float(
        string='Daily Interest Rate (%)',
        help="Lãi suất hàng ngày"
    )

    interest_amount = fields.Monetary(
        string='Interest Amount',
        currency_field='currency_id',
        help="Tiền lãi tính được"
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='calculation_id.currency_id'
    )
