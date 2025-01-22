# models/currency_dashboard.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class CurrencyDashboard(models.Model):
    _name = 'currency.dashboard'
    _description = 'Currency Dashboard'

    name = fields.Char(string='Name', default='Currency Dashboard')
    date = fields.Date(string='Date', default=fields.Date.today)

    total_currencies = fields.Integer(compute='_compute_currency_stats')
    active_currencies = fields.Integer(compute='_compute_currency_stats')
    last_update = fields.Datetime(compute='_compute_currency_stats')

    rate_changes_today = fields.Integer(compute='_compute_rate_changes')
    significant_changes = fields.Integer(compute='_compute_rate_changes')

    @api.depends('date')
    def _compute_currency_stats(self):
        for record in self:
            currencies = self.env['res.currency'].search([])
            active_currencies = currencies.filtered(lambda c: c.active)

            record.total_currencies = len(currencies)
            record.active_currencies = len(active_currencies)

            latest_rate = self.env['res.currency.rate'].search(
                [], order='create_date desc', limit=1)
            record.last_update = latest_rate.create_date if latest_rate else False

    @api.depends('date')
    def _compute_rate_changes(self):
        for record in self:
            today = fields.Date.today()
            yesterday = today - timedelta(days=1)
            changes_today = self.env['res.currency.rate'].search_count([
                ('create_date', '>=', today)
            ])
            record.rate_changes_today = changes_today

            significant = 0
            rates = self.env['res.currency.rate'].search([
                ('create_date', '>=', yesterday)
            ])
            for rate in rates:
                previous_rate = self.env['res.currency.rate'].search([
                    ('currency_id', '=', rate.currency_id.id),
                    ('create_date', '<', rate.create_date)
                ], limit=1)
                if previous_rate and abs((rate.rate - previous_rate.rate) / previous_rate.rate) > 0.01:
                    significant += 1
            record.significant_changes = significant
