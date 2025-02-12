# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    category = fields.Selection([('basic', 'Mặc định / Hóa đơn'),
                                 ('import_export', 'Hải quan'),
                                 ('dpt', 'DPT')], string='Nhóm tiền tệ', default='basic')
    category_code = fields.Char(string='Mã nhóm')
