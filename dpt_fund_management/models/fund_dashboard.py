from odoo import models, fields, api
from odoo import tools

class FundDashboard(models.Model):
    _name = 'dpt.fund.dashboard'
    _description = 'Fund Dashboard'
    _auto = False

    fund_type = fields.Selection([
        ('vn', 'Quỹ VN'),
        ('china', 'Quỹ TQ'),
        ('intermediate', 'Tài khoản trung gian'),
    ], string='Loại quỹ')

    total_balance = fields.Float('Tổng số dư')
    account_count = fields.Integer('Số lượng TK')
    active_count = fields.Integer('TK hoạt động')
    transaction_count = fields.Integer('Số giao dịch')

    currency_id = fields.Many2one('res.currency', 'Tiền tệ')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    fa.fund_type,
                    SUM(fa.balance) as total_balance,
                    COUNT(fa.id) as account_count,
                    COUNT(CASE WHEN fa.is_active THEN 1 END) as active_count,
                    COUNT(ft.id) as transaction_count,
                    fa.currency_id
                FROM dpt_fund_account fa
                LEFT JOIN dpt_fund_transaction ft ON ft.fund_account_id = fa.id
                GROUP BY fa.fund_type, fa.currency_id
            )
        """ % self._table)
