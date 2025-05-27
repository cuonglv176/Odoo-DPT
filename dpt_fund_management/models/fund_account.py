# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


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

    # Computed fields cho smart buttons và thống kê
    transaction_count = fields.Integer(
        string='Số Giao Dịch',
        compute='_compute_transaction_stats',
        store=True
    )

    total_income = fields.Monetary(
        string='Tổng Thu Nhập',
        compute='_compute_transaction_stats',
        store=True,
        currency_field='currency_id'
    )

    total_expense = fields.Monetary(
        string='Tổng Chi Phí',
        compute='_compute_transaction_stats',
        store=True,
        currency_field='currency_id'
    )

    last_transaction_date = fields.Date(
        string='Giao Dịch Cuối',
        compute='_compute_transaction_stats',
        store=True
    )

    available_balance = fields.Monetary(
        string='Số Dư Khả Dụng',
        compute='_compute_available_balance',
        currency_field='currency_id'
    )

    # Fields cho ngân hàng (nếu cần cho import)
    account_type = fields.Selection([
        ('bank', 'Tài khoản ngân hàng'),
        ('cash', 'Tiền mặt'),
        ('investment', 'Đầu tư'),
        ('other', 'Khác')
    ], string='Loại tài khoản', default='cash')

    account_number = fields.Char('Số tài khoản')
    bank_name = fields.Char('Tên ngân hàng')

    def action_import_transactions(self):
        """Mở wizard import giao dịch từ button trong form"""
        self.ensure_one()

        # Kiểm tra loại tài khoản
        if self.account_type != 'bank':
            raise UserError(_('Chỉ có thể import giao dịch cho tài khoản ngân hàng!'))

        # Tạo context với thông tin tài khoản
        context = dict(self.env.context)
        context.update({
            'default_account_id': self.id,
            'default_name': f'Import giao dịch cho {self.name}',
            'account_name': self.name,
            'account_number': self.account_number or '',
            'bank_name': self.bank_name or '',
        })

        # Trả về action mở wizard
        return {
            'name': _('Import Giao Dịch - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.bank.transaction.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
            'view_id': self.env.ref('dpt_fund_management.view_bank_transaction_import_wizard_form').id,
        }

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

    @api.depends('transaction_ids', 'transaction_ids.amount', 'transaction_ids.state')
    def _compute_transaction_stats(self):
        """Tính toán thống kê giao dịch"""
        for record in self:
            confirmed_transactions = record.transaction_ids.filtered(
                lambda t: t.state == 'posted'
            )

            record.transaction_count = len(confirmed_transactions)
            record.total_income = sum(
                t.amount for t in confirmed_transactions
                if t.transaction_type == 'income'
            )
            record.total_expense = abs(sum(
                t.amount for t in confirmed_transactions
                if t.transaction_type == 'expense'
            ))

            if confirmed_transactions:
                record.last_transaction_date = max(
                    confirmed_transactions.mapped('date')
                )
            else:
                record.last_transaction_date = False

    @api.depends('balance')
    def _compute_available_balance(self):
        """Tính số dư khả dụng (có thể trừ pending transactions)"""
        for record in self:
            # Tạm thời = balance, có thể customize sau
            record.available_balance = record.balance

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(f"Mã quỹ '{record.code}' đã tồn tại!")

    def get_balance_in_currency(self):
        """Quy đổi số dư sang VND"""
        self.ensure_one()

        if self.currency_id.name == 'VND':
            raise UserError(_('Tài khoản đã sử dụng VND!'))

        # Tìm tỷ giá mới nhất
        exchange_rate = self.env['dpt.exchange.rate'].search([
            ('from_currency_id', '=', self.currency_id.id),
            ('to_currency_id.name', '=', 'VND'),
            ('is_active', '=', True)
        ], limit=1, order='date desc')

        if exchange_rate:
            balance_vnd = self.balance * exchange_rate.rate
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Quy Đổi Tiền Tệ'),
                    'message': _('Số dư %s %s = %s VND (Tỷ giá: %s)') % (
                        '{:,.0f}'.format(self.balance),
                        self.currency_id.name,
                        '{:,.0f}'.format(balance_vnd),
                        exchange_rate.rate
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi'),
                    'message': _('Không tìm thấy tỷ giá từ %s sang VND') % self.currency_id.name,
                    'type': 'warning'
                }
            }

    def action_view_transactions(self):
        """Xem danh sách giao dịch của quỹ"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Giao Dịch - %s') % self.name,
            'res_model': 'dpt.fund.transaction',
            'view_mode': 'tree,form',
            'domain': [('fund_account_id', '=', self.id)],
            'context': {
                'default_fund_account_id': self.id,
                'search_default_this_month': 1
            },
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    Chưa có giao dịch nào cho tài khoản này!
                </p>
                <p>
                    Tạo giao dịch mới hoặc import từ file Excel.
                </p>
            """
        }

    def action_view_income_transactions(self):
        """Xem giao dịch thu nhập"""
        return self._get_transaction_action('income', 'Thu Nhập')

    def action_view_expense_transactions(self):
        """Xem giao dịch chi phí"""
        return self._get_transaction_action('expense', 'Chi Phí')

    def _get_transaction_action(self, transaction_type, title):
        """Helper method cho action xem giao dịch theo loại"""
        self.ensure_one()

        return {
            'name': _('%s - %s') % (title, self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.fund.transaction',
            'view_mode': 'tree,form',
            'domain': [
                ('fund_account_id', '=', self.id),
                ('transaction_type', '=', transaction_type),
                ('state', '=', 'posted')
            ],
            'context': {
                'default_fund_account_id': self.id,
                'default_transaction_type': transaction_type,
                'search_default_this_month': 1,
            }
        }

    def action_export_transactions(self):
        """Export giao dịch ra Excel"""
        self.ensure_one()

        # Tạo wizard export hoặc direct export
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/export/transactions/{self.id}',
            'target': 'new',
        }

    def action_reconcile_account(self):
        """Đối soát tài khoản"""
        self.ensure_one()

        return {
            'name': _('Đối Soát Tài Khoản - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.fund.reconcile.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_account_id': self.id,
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
