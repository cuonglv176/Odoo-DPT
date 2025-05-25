from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptFundTransaction(models.Model):
    _name = 'dpt.fund.transaction'
    _description = 'Giao dịch Quỹ'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char('Mô tả', required=True, tracking=True)
    date = fields.Date('Ngày giao dịch', required=True, default=fields.Date.today, tracking=True)
    fund_account_id = fields.Many2one('dpt.fund.account', 'Tài khoản quỹ', required=True, tracking=True)
    amount = fields.Float('Số tiền', required=True, tracking=True)
    transaction_type = fields.Selection([
        ('income', 'Thu'),
        ('expense', 'Chi')
    ], string='Loại giao dịch', required=True, tracking=True)

    # Thông tin kế toán
    debit_account_id = fields.Many2one('account.account', 'TK Nợ')
    credit_account_id = fields.Many2one('account.account', 'TK Có')
    journal_entry_id = fields.Many2one('account.move', 'Bút toán')

    # Thông tin tỷ giá (nếu có)
    exchange_rate_id = fields.Many2one('dpt.exchange.rate', 'Tỷ giá')
    original_amount = fields.Float('Số tiền gốc')
    original_currency_id = fields.Many2one('res.currency', 'Tiền tệ gốc')

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('posted', 'Đã ghi sổ')
    ], default='draft', tracking=True)

    def action_confirm(self):
        self.state = 'confirmed'
        self._create_journal_entry()

    def action_post(self):
        if self.journal_entry_id:
            self.journal_entry_id.action_post()
            self.state = 'posted'

    def _create_journal_entry(self):
        """Tạo bút toán kế toán"""
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            raise ValidationError('Không tìm thấy nhật ký kế toán phù hợp!')

        move_vals = {
            'journal_id': journal.id,
            'date': self.date,
            'ref': self.name,
            'line_ids': []
        }

        # Xác định tài khoản nợ và có
        if self.transaction_type == 'income':
            debit_account = self.fund_account_id.account_id
            credit_account = self.credit_account_id or self.debit_account_id
        else:
            debit_account = self.debit_account_id or self.credit_account_id
            credit_account = self.fund_account_id.account_id

        # Tạo dòng nợ
        move_vals['line_ids'].append((0, 0, {
            'account_id': debit_account.id,
            'debit': self.amount,
            'credit': 0,
            'name': self.name,
        }))

        # Tạo dòng có
        move_vals['line_ids'].append((0, 0, {
            'account_id': credit_account.id,
            'debit': 0,
            'credit': self.amount,
            'name': self.name,
        }))

        move = self.env['account.move'].create(move_vals)
        self.journal_entry_id = move.id
