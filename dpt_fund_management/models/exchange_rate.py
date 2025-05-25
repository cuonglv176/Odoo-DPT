from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptExchangeRate(models.Model):
    _name = 'dpt.exchange.rate'
    _description = 'Tỷ giá hối đoái'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char('Tên', compute='_compute_name', store=True)
    date = fields.Date('Ngày', required=True, default=fields.Date.today, tracking=True)
    from_currency_id = fields.Many2one('res.currency', 'Từ tiền tệ', required=True, tracking=True)
    to_currency_id = fields.Many2one('res.currency', 'Sang tiền tệ', required=True, tracking=True)
    rate = fields.Float('Tỷ giá', required=True, digits=(12, 6), tracking=True)

    # Tỷ giá Vietinbank
    vietinbank_buy = fields.Float('VTB - Mua vào', digits=(12, 2))
    vietinbank_sell = fields.Float('VTB - Bán ra', digits=(12, 2))
    margin = fields.Float('Chênh lệch', default=65)

    source = fields.Selection([
        ('manual', 'Nhập thủ công'),
        ('vietinbank', 'Vietinbank'),
        ('system', 'Hệ thống')
    ], default='manual', tracking=True)

    is_active = fields.Boolean('Hoạt động', default=True, tracking=True)

    # Relations
    transaction_ids = fields.One2many('dpt.fund.transaction', 'exchange_rate_id', 'Giao dịch sử dụng')
    transfer_ids = fields.One2many('dpt.fund.transfer', 'exchange_rate_id', 'Chuyển tiền sử dụng')

    @api.depends('from_currency_id', 'to_currency_id', 'date')
    def _compute_name(self):
        for record in self:
            if record.from_currency_id and record.to_currency_id:
                record.name = f"{record.from_currency_id.name}/{record.to_currency_id.name} - {record.date}"
            else:
                record.name = "Tỷ giá mới"

    @api.constrains('rate')
    def _check_rate(self):
        for record in self:
            if record.rate <= 0:
                raise ValidationError('Tỷ giá phải lớn hơn 0!')

    @api.constrains('from_currency_id', 'to_currency_id')
    def _check_different_currencies(self):
        for record in self:
            if record.from_currency_id.id == record.to_currency_id.id:
                raise ValidationError('Tiền tệ nguồn và đích phải khác nhau!')

    def get_latest_rate(self, from_currency, to_currency, date=None):
        """Lấy tỷ giá mới nhất"""
        if not date:
            date = fields.Date.today()

        rate = self.search([
            ('from_currency_id', '=', from_currency),
            ('to_currency_id', '=', to_currency),
            ('date', '<=', date),
            ('is_active', '=', True)
        ], order='date desc', limit=1)

        return rate.rate if rate else 1.0
