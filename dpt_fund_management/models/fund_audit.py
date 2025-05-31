from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptFundAudit(models.Model):
    _name = 'dpt.fund.audit'
    _description = 'Kiểm kê Quỹ'
    _inherit = ['mail.thread']
    _order = 'audit_date desc'

    name = fields.Char('Số phiếu kiểm kê', required=True, tracking=True)
    audit_date = fields.Date('Ngày kiểm kê', required=True, default=fields.Date.today, tracking=True)
    auditor_id = fields.Many2one('res.users', 'Người kiểm kê', required=True, default=lambda self: self.env.user,
                                 tracking=True)

    # Thông tin kiểm kê
    fund_account_id = fields.Many2one('dpt.fund.account', 'Tài khoản quỹ', required=True, tracking=True)
    book_balance = fields.Float('Số dư sổ sách', compute='_compute_book_balance', store=True)
    actual_balance = fields.Float('Số dư thực tế', required=True, tracking=True)
    difference = fields.Float('Chênh lệch', compute='_compute_difference', store=True)

    # Phân tích chênh lệch
    difference_type = fields.Selection([
        ('surplus', 'Thừa tiền'),
        ('shortage', 'Thiếu tiền'),
        ('match', 'Khớp')
    ], compute='_compute_difference_type', store=True)

    reason = fields.Text('Lý do chênh lệch')
    adjustment_needed = fields.Boolean('Cần điều chỉnh', compute='_compute_adjustment_needed', store=True)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('audited', 'Đã kiểm kê'),
        ('adjusted', 'Đã điều chỉnh'),
        ('approved', 'Đã duyệt')
    ], default='draft', tracking=True)

    # Chi tiết kiểm kê
    audit_line_ids = fields.One2many('dpt.fund.audit.line', 'audit_id', 'Chi tiết kiểm kê')
    adjustment_entry_id = fields.Many2one('account.move', 'Bút toán điều chỉnh')

    @api.depends('fund_account_id', 'audit_date')
    def _compute_book_balance(self):
        for record in self:
            if record.fund_account_id:
                # Tính số dư sổ sách tại ngày kiểm kê
                transactions = record.fund_account_id.transaction_ids.filtered(
                    lambda x: x.date <= record.audit_date and x.state in ['confirmed', 'posted']
                )
                income = sum(transactions.filtered(lambda x: x.transaction_type == 'income').mapped('amount'))
                expense = sum(transactions.filtered(lambda x: x.transaction_type == 'expense').mapped('amount'))
                record.book_balance = income - expense
            else:
                record.book_balance = 0

    @api.depends('book_balance', 'actual_balance')
    def _compute_difference(self):
        for record in self:
            record.difference = record.actual_balance - record.book_balance

    @api.depends('difference')
    def _compute_difference_type(self):
        for record in self:
            if record.difference > 0:
                record.difference_type = 'surplus'
            elif record.difference < 0:
                record.difference_type = 'shortage'
            else:
                record.difference_type = 'match'

    @api.depends('difference')
    def _compute_adjustment_needed(self):
        for record in self:
            record.adjustment_needed = abs(record.difference) > 0.01

    def action_audit(self):
        """Thực hiện kiểm kê"""
        self.state = 'audited'

    def action_create_adjustment(self):
        """Tạo bút toán điều chỉnh"""
        if not self.adjustment_needed:
            raise ValidationError('Không cần điều chỉnh!')

        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            raise ValidationError('Không tìm thấy nhật ký kế toán!')

        move_vals = {
            'journal_id': journal.id,
            'date': self.audit_date,
            'ref': f'Điều chỉnh kiểm kê - {self.name}',
            'line_ids': []
        }

        # Tài khoản chênh lệch
        diff_account = self.env['account.account'].search([('code', '=', '515')], limit=1)
        if not diff_account:
            raise ValidationError('Không tìm thấy tài khoản chênh lệch (515)!')

        if self.difference > 0:  # Thừa tiền
            # Nợ TK Quỹ / Có TK Chênh lệch
            move_vals['line_ids'].append((0, 0, {
                'account_id': self.fund_account_id.account_id.id,
                'debit': abs(self.difference),
                'credit': 0,
                'name': f'Điều chỉnh thừa tiền - {self.name}',
            }))
            move_vals['line_ids'].append((0, 0, {
                'account_id': diff_account.id,
                'debit': 0,
                'credit': abs(self.difference),
                'name': f'Điều chỉnh thừa tiền - {self.name}',
            }))
        else:  # Thiếu tiền
            # Nợ TK Chênh lệch / Có TK Quỹ
            move_vals['line_ids'].append((0, 0, {
                'account_id': diff_account.id,
                'debit': abs(self.difference),
                'credit': 0,
                'name': f'Điều chỉnh thiếu tiền - {self.name}',
            }))
            move_vals['line_ids'].append((0, 0, {
                'account_id': self.fund_account_id.account_id.id,
                'debit': 0,
                'credit': abs(self.difference),
                'name': f'Điều chỉnh thiếu tiền - {self.name}',
            }))

        move = self.env['account.move'].create(move_vals)
        self.adjustment_entry_id = move.id
        self.state = 'adjusted'

    def action_approve(self):
        """Duyệt kiểm kê"""
        if self.adjustment_entry_id and self.adjustment_entry_id.state == 'draft':
            self.adjustment_entry_id.action_post()
        self.state = 'approved'


class DptFundAuditLine(models.Model):
    _name = 'dpt.fund.audit.line'
    _description = 'Chi tiết kiểm kê quỹ'

    audit_id = fields.Many2one('dpt.fund.audit', 'Phiếu kiểm kê', required=True, ondelete='cascade')
    denomination = fields.Selection([
        ('500000', '500,000'),
        ('200000', '200,000'),
        ('100000', '100,000'),
        ('50000', '50,000'),
        ('20000', '20,000'),
        ('10000', '10,000'),
        ('5000', '5,000'),
        ('2000', '2,000'),
        ('1000', '1,000'),
        ('500', '500'),
        ('200', '200'),
        ('100', '100'),
    ], string='Mệnh giá', required=True)

    quantity = fields.Integer('Số lượng', default=0)
    amount = fields.Float('Thành tiền', compute='_compute_amount', store=True)

    @api.depends('denomination', 'quantity')
    def _compute_amount(self):
        for record in self:
            if record.denomination and record.quantity:
                record.amount = float(record.denomination) * record.quantity
            else:
                record.amount = 0
