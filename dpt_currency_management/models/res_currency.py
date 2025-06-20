# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResCurrency(models.Model):
    _name = 'res.currency'
    _inherit = ['res.currency', 'mail.thread', 'mail.activity.mixin']
    _description = 'Currency'

    name = fields.Char(tracking=True)
    symbol = fields.Char(tracking=True)
    rate = fields.Float(tracking=True)
    rate_ids = fields.One2many(tracking=True)
    active = fields.Boolean(tracking=True)
    position = fields.Selection(tracking=True)
    date = fields.Date(tracking=True)
    currency_unit_label = fields.Char(tracking=True)
    currency_subunit_label = fields.Char(tracking=True)
    rounding = fields.Float(tracking=True)
    decimal_places = fields.Integer(tracking=True)
    full_name = fields.Char(tracking=True)
    
    category = fields.Selection([('basic', 'Mặc định / Hóa đơn'),
                                 ('import_export', 'Hải quan'),
                                 ('dpt', 'DPT')], string='Nhóm tiền tệ', default='basic', tracking=True)
    category_code = fields.Char(string='Mã nhóm', tracking=True)
