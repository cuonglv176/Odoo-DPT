from odoo import models, fields, api
from datetime import datetime, timedelta


class FundDashboard(models.Model):
    _name = 'dpt.fund.dashboard'
    _description = 'Fund Management Dashboard'

    name = fields.Char(string='Dashboard Name', required=True, default='Fund Dashboard')
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='To Date', default=fields.Date.today)

    # Summary fields
    total_balance = fields.Monetary(string='Total Balance', compute='_compute_summary', store=False)
    total_income = fields.Monetary(string='Total Income', compute='_compute_summary', store=False)
    total_expense = fields.Monetary(string='Total Expense', compute='_compute_summary', store=False)
    net_profit = fields.Monetary(string='Net Profit', compute='_compute_summary', store=False)

    # Performance metrics
    roi_percentage = fields.Float(string='ROI Percentage', compute='_compute_metrics', store=False)
    liquidity_ratio = fields.Float(string='Liquidity Ratio', compute='_compute_metrics', store=False)
    diversification_score = fields.Float(string='Diversification Score', compute='_compute_metrics', store=False)

    # Alerts
    pending_transfers = fields.Integer(string='Pending Transfers', compute='_compute_alerts', store=False)

    # Currency
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    @api.depends('date_from', 'date_to')
    def _compute_summary(self):
        for record in self:
            # Kiểm tra xem model dpt.fund.account có tồn tại không
            if 'dpt.fund.account' in self.env:
                # Tìm tất cả accounts (bỏ filter state vì field không tồn tại)
                accounts = self.env['dpt.fund.account'].search([])
                record.total_balance = sum(accounts.mapped('balance'))
            else:
                record.total_balance = 0.0

            # Tính toán income và expense từ transactions
            if 'dpt.fund.transaction' in self.env:
                domain = []
                if record.date_from:
                    domain.append(('date', '>=', record.date_from))
                if record.date_to:
                    domain.append(('date', '<=', record.date_to))

                transactions = self.env['dpt.fund.transaction'].search(domain)

                # Tính income (credit) và expense (debit)
                income_transactions = transactions.filtered(lambda t: t.amount > 0)
                expense_transactions = transactions.filtered(lambda t: t.amount < 0)

                record.total_income = sum(income_transactions.mapped('amount'))
                record.total_expense = abs(sum(expense_transactions.mapped('amount')))
            else:
                record.total_income = 0.0
                record.total_expense = 0.0

            record.net_profit = record.total_income - record.total_expense

    @api.depends('total_balance', 'total_income', 'total_expense')
    def _compute_metrics(self):
        for record in self:
            # ROI Percentage
            if record.total_balance > 0:
                record.roi_percentage = (record.net_profit / record.total_balance) * 100
            else:
                record.roi_percentage = 0.0

            # Liquidity Ratio (giả sử = total_balance / total_expense)
            if record.total_expense > 0:
                record.liquidity_ratio = record.total_balance / record.total_expense
            else:
                record.liquidity_ratio = 0.0

            # Diversification Score (giả sử dựa trên số lượng accounts)
            if 'dpt.fund.account' in self.env:
                account_count = self.env['dpt.fund.account'].search_count([])
                record.diversification_score = min(account_count * 10, 100)  # Max 100%
            else:
                record.diversification_score = 0.0

    @api.depends('date_from', 'date_to')
    def _compute_alerts(self):
        for record in self:
            # Đếm pending transfers
            if 'dpt.fund.transfer' in self.env:
                # Kiểm tra xem có field state không
                transfer_model = self.env['dpt.fund.transfer']
                if 'state' in transfer_model._fields:
                    record.pending_transfers = transfer_model.search_count([('state', '=', 'pending')])
                else:
                    record.pending_transfers = transfer_model.search_count([])
            else:
                record.pending_transfers = 0

    def refresh_dashboard(self):
        """Refresh dashboard data"""
        self._compute_summary()
        self._compute_metrics()
        self._compute_alerts()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # Action methods for buttons
    def action_view_accounts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fund Accounts',
            'res_model': 'dpt.fund.account',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_view_transactions(self):
        domain = []
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transactions',
            'res_model': 'dpt.fund.transaction',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }

    def action_view_transfers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'res_model': 'dpt.fund.transfer',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_new_account(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Account',
            'res_model': 'dpt.fund.account',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_new_transaction(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Transaction',
            'res_model': 'dpt.fund.transaction',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_new_transfer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Transfer',
            'res_model': 'dpt.fund.transfer',
            'view_mode': 'form',
            'target': 'new',
        }
