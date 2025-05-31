from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptFundTransfer(models.Model):
    _name = 'dpt.fund.transfer'
    _description = 'Chuyển tiền giữa các quỹ'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char('Số chứng từ', required=True, tracking=True)
    date = fields.Date('Ngày chuyển', required=True, default=fields.Date.today, tracking=True)

    from_fund_id = fields.Many2one('dpt.fund.account', 'Quỹ chuyển', required=True, tracking=True)
    to_fund_id = fields.Many2one('dpt.fund.account', 'Quỹ nhận', required=True, tracking=True)

    amount = fields.Float('Số tiền chuyển', required=True, tracking=True)
    from_currency_id = fields.Many2one('res.currency', 'Tiền tệ chuyển', related='from_fund_id.currency_id')
    to_currency_id = fields.Many2one('res.currency', 'Tiền tệ nhận', related='to_fund_id.currency_id')

    exchange_rate_id = fields.Many2one('dpt.exchange.rate', 'Tỷ giá áp dụng')
    converted_amount = fields.Float('Số tiền sau quy đổi', compute='_compute_converted_amount', store=True)

    # Thông tin ngân hàng
    bank_fee = fields.Float('Phí ngân hàng', default=65)
    actual_received = fields.Float('Số tiền thực nhận', compute='_compute_actual_received', store=True)

    description = fields.Text('Mô tả')

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Đang chuyển'),
        ('received', 'Đã nhận'),
        ('cancelled', 'Đã hủy')
    ], default='draft', tracking=True)

    # Theo dõi giao dịch
    debit_transaction_id = fields.Many2one('dpt.fund.transaction', 'Giao dịch ghi nợ')
    credit_transaction_id = fields.Many2one('dpt.fund.transaction', 'Giao dịch ghi có')
    pending_transfer_id = fields.Many2one('dpt.pending.transfer', 'Tiền đang chuyển')

    @api.depends('amount', 'exchange_rate_id')
    def _compute_converted_amount(self):
        for record in self:
            if record.exchange_rate_id:
                record.converted_amount = record.amount * record.exchange_rate_id.rate
            else:
                record.converted_amount = record.amount

    @api.depends('converted_amount', 'bank_fee')
    def _compute_actual_received(self):
        for record in self:
            record.actual_received = record.converted_amount - record.bank_fee

    def action_send_transfer(self):
        """Gửi tiền chuyển"""
        # Tạo giao dịch ghi nợ quỹ gửi
        debit_transaction = self.env['dpt.fund.transaction'].create({
            'name': f'Chuyển tiền - {self.name}',
            'date': self.date,
            'fund_account_id': self.from_fund_id.id,
            'amount': self.amount,
            'transaction_type': 'expense',
        })
        debit_transaction.action_confirm()
        self.debit_transaction_id = debit_transaction.id

        # Tạo bản ghi tiền đang chuyển
        pending_transfer = self.env['dpt.pending.transfer'].create({
            'transfer_id': self.id,
            'amount': self.amount,
            'currency_id': self.from_currency_id.id,
            'date_sent': self.date,
        })
        self.pending_transfer_id = pending_transfer.id

        self.state = 'pending'

    def action_confirm_received(self):
        """Xác nhận đã nhận tiền"""
        # Tạo giao dịch ghi có quỹ nhận
        credit_transaction = self.env['dpt.fund.transaction'].create({
            'name': f'Nhận tiền chuyển - {self.name}',
            'date': fields.Date.today(),
            'fund_account_id': self.to_fund_id.id,
            'amount': self.actual_received,
            'transaction_type': 'income',
        })
        credit_transaction.action_confirm()
        self.credit_transaction_id = credit_transaction.id

        # Cập nhật trạng thái tiền đang chuyển
        if self.pending_transfer_id:
            self.pending_transfer_id.state = 'received'
            self.pending_transfer_id.date_received = fields.Date.today()

        self.state = 'received'

    @api.constrains('from_fund_id', 'to_fund_id')
    def _check_different_funds(self):
        for record in self:
            if record.from_fund_id.id == record.to_fund_id.id:
                raise ValidationError('Quỹ chuyển và quỹ nhận phải khác nhau!')
