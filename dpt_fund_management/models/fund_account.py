from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptFundAccount(models.Model):
    _name = 'dpt.fund.account'
    _description = 'Tài khoản Quỹ'
    _inherit = ['mail.thread']

    name = fields.Char('Tên quỹ', required=True, tracking=True)
    code = fields.Char('Mã quỹ', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Tiền tệ', required=True, tracking=True)
    account_id = fields.Many2one('account.account', 'Tài khoản kế toán', required=True)
    balance = fields.Float('Số dư', compute='_compute_balance', store=True)
    fund_type = fields.Selection([
        ('vn', 'Quỹ VN'),
        ('china', 'Quỹ TQ'),
        ('intermediate', 'Tài khoản trung gian')
    ], string='Loại quỹ', required=True, tracking=True)
    is_active = fields.Boolean('Hoạt động', default=True, tracking=True)

    # Relations
    transaction_ids = fields.One2many('dpt.fund.transaction', 'fund_account_id', 'Giao dịch')
    transfer_from_ids = fields.One2many('dpt.fund.transfer', 'from_fund_id', 'Chuyển đi')
    transfer_to_ids = fields.One2many('dpt.fund.transfer', 'to_fund_id', 'Chuyển đến')

    @api.depends('transaction_ids.amount', 'transaction_ids.transaction_type', 'transaction_ids.state')
    def _compute_balance(self):
        for record in self:
            confirmed_transactions = record.transaction_ids.filtered(lambda x: x.state in ['confirmed', 'posted'])
            income = sum(confirmed_transactions.filtered(lambda x: x.transaction_type == 'income').mapped('amount'))
            expense = sum(confirmed_transactions.filtered(lambda x: x.transaction_type == 'expense').mapped('amount'))
            record.balance = income - expense

    @api.constrains('code')
    def _check_unique_code(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError('Mã quỹ phải là duy nhất!')

    def get_balance_in_currency(self, target_currency_id):
        """Lấy số dư quy đổi theo tiền tệ chỉ định"""
        if self.currency_id.id == target_currency_id:
            return self.balance

        # Tìm tỷ giá mới nhất
        exchange_rate = self.env['dpt.exchange.rate'].search([
            ('from_currency_id', '=', self.currency_id.id),
            ('to_currency_id', '=', target_currency_id),
            ('date', '<=', fields.Date.today())
        ], order='date desc', limit=1)

        if exchange_rate:
            return self.balance * exchange_rate.rate
        return 0
