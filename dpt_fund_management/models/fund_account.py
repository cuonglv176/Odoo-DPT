# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptFundAccount(models.Model):
    _name = 'dpt.fund.account'
    _description = 'Tài khoản Quỹ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, name'

    name = fields.Char('Tên quỹ', required=True, tracking=True)
    code = fields.Char('Mã quỹ', required=True, tracking=True)
    fund_type = fields.Selection([
        ('vn', 'Quỹ VN'),
        ('china', 'Quỹ TQ'),
        ('intermediate', 'Tài khoản trung gian')
    ], string='Loại quỹ', required=True, tracking=True)

    currency_id = fields.Many2one('res.currency', string='Tiền tệ', required=True,
                                  default=lambda self: self.env.company.currency_id)
    account_id = fields.Many2one('account.account', string='Tài khoản kế toán',
                                 domain=[('account_type', '=', 'asset_cash')])

    balance = fields.Monetary('Số dư', currency_field='currency_id',
                              compute='_compute_balance', store=True)
    is_active = fields.Boolean('Hoạt động', default=True, tracking=True)

    # Relations
    transaction_ids = fields.One2many('dpt.fund.transaction', 'fund_account_id',
                                      string='Giao dịch')
    transfer_from_ids = fields.One2many('dpt.fund.transfer', 'from_fund_id',
                                        string='Chuyển đi')
    transfer_to_ids = fields.One2many('dpt.fund.transfer', 'to_fund_id',
                                      string='Chuyển đến')

    @api.depends('transaction_ids.amount', 'transaction_ids.state',
                 'transfer_from_ids.amount', 'transfer_from_ids.state',
                 'transfer_to_ids.converted_amount', 'transfer_to_ids.state')
    def _compute_balance(self):
        for record in self:
            balance = 0.0

            # Tính từ giao dịch
            posted_transactions = record.transaction_ids.filtered(lambda t: t.state == 'posted')
            for transaction in posted_transactions:
                if transaction.transaction_type == 'income':
                    balance += transaction.amount
                else:  # expense
                    balance -= transaction.amount

            # Tính từ chuyển tiền đi (trừ)
            sent_transfers = record.transfer_from_ids.filtered(lambda t: t.state in ['pending', 'received'])
            balance -= sum(sent_transfers.mapped('amount'))

            # Tính từ chuyển tiền đến (cộng)
            received_transfers = record.transfer_to_ids.filtered(lambda t: t.state == 'received')
            balance += sum(received_transfers.mapped('converted_amount'))

            record.balance = balance

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(f"Mã quỹ '{record.code}' đã tồn tại!")

    def get_balance_in_currency(self):
        """Quy đổi số dư sang VND"""
        for record in self:
            if record.currency_id.name == 'VND':
                continue

            # Tìm tỷ giá mới nhất
            exchange_rate = self.env['dpt.exchange.rate'].search([
                ('from_currency_id', '=', record.currency_id.id),
                ('to_currency_id.name', '=', 'VND'),
                ('is_active', '=', True)
            ], limit=1, order='date desc')

            if exchange_rate:
                balance_vnd = record.balance * exchange_rate.rate
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Quy đổi VND',
                        'message': f'Số dư {record.balance:,.0f} {record.currency_id.name} = {balance_vnd:,.0f} VND (Tỷ giá: {exchange_rate.rate})',
                        'type': 'info'
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi',
                        'message': f'Không tìm thấy tỷ giá từ {record.currency_id.name} sang VND',
                        'type': 'warning'
                    }
                }

    def action_view_transactions(self):
        """Xem danh sách giao dịch của quỹ"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Giao dịch - {self.name}',
            'res_model': 'dpt.fund.transaction',
            'view_mode': 'tree,form',
            'domain': [('fund_account_id', '=', self.id)],
            'context': {
                'default_fund_account_id': self.id,
                'search_default_this_month': 1
            }
        }

    @api.model
    def create(self, vals):
        # Auto generate code if not provided
        if not vals.get('code'):
            fund_type = vals.get('fund_type', '')
            if fund_type == 'vn':
                prefix = 'VN'
            elif fund_type == 'china':
                prefix = 'CN'
            else:
                prefix = 'IT'

            sequence = self.env['ir.sequence'].next_by_code('dpt.fund.account') or '001'
            vals['code'] = f'{prefix}{sequence}'

        return super().create(vals)

    def name_get(self):
        result = []
        for record in self:
            name = f'[{record.code}] {record.name}'
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if domain is None:
            domain = []

        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)] + domain

        return self._search(domain, limit=limit, order=order)
