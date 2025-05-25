from odoo import models, fields, api
from datetime import datetime, timedelta
import json


class FundDashboard(models.Model):
    _name = 'dpt.fund.dashboard'
    _description = 'Fund Management Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Dashboard Name', default='Fund Management Dashboard')
    date_from = fields.Date(string='From Date', default=fields.Date.today().replace(day=1))
    date_to = fields.Date(string='To Date', default=fields.Date.today())

    # Summary Fields
    total_balance = fields.Float(string='Total Balance', compute='_compute_summary')
    total_income = fields.Float(string='Total Income', compute='_compute_summary')
    total_expense = fields.Float(string='Total Expense', compute='_compute_summary')
    net_profit = fields.Float(string='Net Profit', compute='_compute_summary')
    pending_transfers = fields.Integer(string='Pending Transfers', compute='_compute_summary')

    # Performance Metrics
    roi_percentage = fields.Float(string='ROI (%)', compute='_compute_performance')
    liquidity_ratio = fields.Float(string='Liquidity Ratio', compute='_compute_performance')
    diversification_score = fields.Float(string='Diversification Score', compute='_compute_performance')

    # Charts Data
    account_distribution_chart = fields.Text(string='Account Distribution Chart', compute='_compute_charts')
    monthly_performance_chart = fields.Text(string='Monthly Performance Chart', compute='_compute_charts')
    transaction_trend_chart = fields.Text(string='Transaction Trend Chart', compute='_compute_charts')

    @api.depends('date_from', 'date_to')
    def _compute_summary(self):
        for record in self:
            # Total Balance from all active accounts
            accounts = self.env['dpt.fund.account'].search([('state', '=', 'active')])
            record.total_balance = sum(accounts.mapped('balance'))

            # Income and Expense from transactions
            domain = [
                ('transaction_date', '>=', record.date_from),
                ('transaction_date', '<=', record.date_to),
                ('state', '=', 'posted')
            ]

            transactions = self.env['dpt.fund.transaction'].search(domain)
            record.total_income = sum(transactions.filtered(lambda t: t.transaction_type == 'income').mapped('amount'))
            record.total_expense = sum(
                transactions.filtered(lambda t: t.transaction_type == 'expense').mapped('amount'))
            record.net_profit = record.total_income - record.total_expense

            # Pending transfers
            record.pending_transfers = self.env['dpt.fund.transfer'].search_count([('state', '=', 'pending')])

    @api.depends('total_income', 'total_expense', 'total_balance')
    def _compute_performance(self):
        for record in self:
            # ROI calculation
            if record.total_balance > 0:
                record.roi_percentage = (record.net_profit / record.total_balance) * 100
            else:
                record.roi_percentage = 0

            # Liquidity ratio (cash + bank / monthly expenses)
            cash_accounts = self.env['dpt.fund.account'].search([
                ('account_type', 'in', ['cash', 'bank']),
                ('state', '=', 'active')
            ])
            liquid_balance = sum(cash_accounts.mapped('balance'))
            days_diff = (record.date_to - record.date_from).days or 1
            monthly_expense = record.total_expense / max(1, days_diff / 30)
            record.liquidity_ratio = liquid_balance / max(1, monthly_expense) if monthly_expense > 0 else 0

            # Diversification score
            account_types = self.env['dpt.fund.account'].search([('state', '=', 'active')]).mapped('account_type')
            unique_types = len(set(account_types))
            total_possible_types = 4  # cash, bank, investment, credit
            record.diversification_score = (unique_types / total_possible_types) * 100

    @api.depends('date_from', 'date_to')
    def _compute_charts(self):
        for record in self:
            # Account Distribution Chart
            accounts = self.env['dpt.fund.account'].search([('state', '=', 'active')])
            account_data = {}
            for account in accounts:
                if account.account_type not in account_data:
                    account_data[account.account_type] = 0
                account_data[account.account_type] += account.balance

            record.account_distribution_chart = json.dumps({
                'labels': list(account_data.keys()),
                'datasets': [{
                    'data': list(account_data.values()),
                    'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                }]
            }) if account_data else json.dumps({})

            # Monthly Performance Chart
            monthly_data = record._get_monthly_performance()
            record.monthly_performance_chart = json.dumps(monthly_data)

            # Transaction Trend Chart
            trend_data = record._get_transaction_trend()
            record.transaction_trend_chart = json.dumps(trend_data)

    def _get_monthly_performance(self):
        """Get monthly performance data for the last 12 months"""
        data = {'labels': [], 'income': [], 'expense': [], 'profit': []}

        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            transactions = self.env['dpt.fund.transaction'].search([
                ('transaction_date', '>=', month_start.date()),
                ('transaction_date', '<=', month_end.date()),
                ('state', '=', 'posted')
            ])

            income = sum(transactions.filtered(lambda t: t.transaction_type == 'income').mapped('amount'))
            expense = sum(transactions.filtered(lambda t: t.transaction_type == 'expense').mapped('amount'))

            data['labels'].insert(0, month_start.strftime('%b %Y'))
            data['income'].insert(0, income)
            data['expense'].insert(0, expense)
            data['profit'].insert(0, income - expense)

        return {
            'labels': data['labels'],
            'datasets': [
                {
                    'label': 'Income',
                    'data': data['income'],
                    'backgroundColor': '#36A2EB'
                },
                {
                    'label': 'Expense',
                    'data': data['expense'],
                    'backgroundColor': '#FF6384'
                },
                {
                    'label': 'Profit',
                    'data': data['profit'],
                    'backgroundColor': '#4BC0C0'
                }
            ]
        }

    def _get_transaction_trend(self):
        """Get daily transaction trend for the selected period"""
        transactions = self.env['dpt.fund.transaction'].search([
            ('transaction_date', '>=', self.date_from),
            ('transaction_date', '<=', self.date_to),
            ('state', '=', 'posted')
        ])

        daily_data = {}
        current_date = self.date_from
        while current_date <= self.date_to:
            daily_transactions = transactions.filtered(lambda t: t.transaction_date == current_date)
            daily_data[current_date.strftime('%Y-%m-%d')] = len(daily_transactions)
            current_date += timedelta(days=1)

        return {
            'labels': list(daily_data.keys()),
            'datasets': [{
                'label': 'Daily Transactions',
                'data': list(daily_data.values()),
                'borderColor': '#36A2EB',
                'fill': False
            }]
        }

    def get_alert_data(self):
        """Get alert data for dashboard"""
        alerts = []

        # Low liquidity alert
        if self.liquidity_ratio < 2:
            alerts.append({
                'type': 'danger',
                'title': 'Low Liquidity',
                'message': f'Liquidity ratio is {self.liquidity_ratio:.2f}, below safe threshold of 2.0'
            })

        # High expense alert
        if self.total_expense > self.total_income * 0.8:
            alerts.append({
                'type': 'warning',
                'title': 'High Expenses',
                'message': 'Expenses are more than 80% of income'
            })

        # Pending transfers alert
        if self.pending_transfers > 10:
            alerts.append({
                'type': 'info',
                'title': 'Pending Transfers',
                'message': f'{self.pending_transfers} transfers are pending approval'
            })

        return alerts

    def refresh_dashboard(self):
        """Refresh dashboard data - Button method"""
        self._compute_summary()
        self._compute_performance()
        self._compute_charts()
        self.message_post(body="Dashboard data refreshed successfully")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Dashboard data has been refreshed!',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def get_dashboard_data(self):
        """API method to get all dashboard data"""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})

        return {
            'summary': {
                'total_balance': dashboard.total_balance,
                'total_income': dashboard.total_income,
                'total_expense': dashboard.total_expense,
                'net_profit': dashboard.net_profit,
                'pending_transfers': dashboard.pending_transfers,
                'roi_percentage': dashboard.roi_percentage,
                'liquidity_ratio': dashboard.liquidity_ratio,
                'diversification_score': dashboard.diversification_score,
            },
            'charts': {
                'account_distribution': json.loads(dashboard.account_distribution_chart or '{}'),
                'monthly_performance': json.loads(dashboard.monthly_performance_chart or '{}'),
                'transaction_trend': json.loads(dashboard.transaction_trend_chart or '{}'),
            },
            'alerts': dashboard.get_alert_data(),
        }

    def action_view_accounts(self):
        """Action to view fund accounts"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fund Accounts',
            'res_model': 'dpt.fund.account',
            'view_mode': 'tree,form',
            'domain': [('state', '=', 'active')],
        }

    def action_view_transactions(self):
        """Action to view transactions"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transactions',
            'res_model': 'dpt.fund.transaction',
            'view_mode': 'tree,form',
            'domain': [
                ('transaction_date', '>=', self.date_from),
                ('transaction_date', '<=', self.date_to)
            ],
        }

    def action_view_transfers(self):
        """Action to view transfers"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fund Transfers',
            'res_model': 'dpt.fund.transfer',
            'view_mode': 'tree,form',
            'domain': [('state', '=', 'pending')],
        }

    def action_new_account(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Fund Account',
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
