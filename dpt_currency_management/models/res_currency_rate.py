# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResCurrencyRate(models.Model):
    _name = 'res.currency.rate'
    _inherit = ['res.currency.rate', 'mail.thread', 'mail.activity.mixin']
    _description = 'Currency Rate'

    name = fields.Date(tracking=True) 
    rate = fields.Float(tracking=True)
    company_id = fields.Many2one(tracking=True)
    currency_id = fields.Many2one(tracking=True)
    write_date = fields.Datetime(tracking=True) 