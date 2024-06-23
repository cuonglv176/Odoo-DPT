# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import collections
from datetime import timedelta
from itertools import groupby
import operator as py_operator
from odoo import fields, models, _
from odoo.tools import groupby
from odoo.tools.float_utils import float_round, float_is_zero


class DptExportImport(models.Model):
    _name = "dpt.export.import"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import'

    name = fields.Char(string='Title')
    code = fields.Char(string='Code')
    user_id = fields.Many2one('res.user', string='User Export/Import', default=lambda self: self.env.user)
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    line_ids = fields.One2many('dpt.export.import.line', 'export_import_id', string='Export/Import Line')


class DptExportImportLine(models.Model):
    _name = "dpt.export.import.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import line'

    export_import_id = fields.Many2one('dpt.export.import', string='Export import')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id')
    product_id = fields.Many2one('product.product', string='Product')
    dpt_english_name = fields.Char(string='English name', tracking=True)
    dpt_description = fields.Text(string='Description Product', size=120, tracking=True)
    dpt_n_w_kg = fields.Char(string='N.W (KG)', tracking=True)
    dpt_g_w_kg = fields.Char(string='G.W (KG)', tracking=True)
    dpt_uom_id = fields.Many2one('uom.uom', string='Uom Export/Import', tracking=True)
    dpt_uom2_ecus_id = fields.Many2one('uom.uom', string='ĐVT SL2 (Ecus)', tracking=True)
    dpt_uom2_id = fields.Many2one('uom.uom', string='ĐVT 2', tracking=True)
    dpt_price_kd = fields.Monetary(string='Giá KD/giá cũ', tracking=True)
    dpt_price_usd = fields.Monetary(string='Giá khai (USD)', tracking=True)
    dpt_tax_import = fields.Float(string='Tax import (%)', tracking=True)
    dpt_tax_ecus5 = fields.Float(string='VAT ECUS5', tracking=True)
    dpt_tax = fields.Float(string='VAT(%)', tracking=True)
    dpt_exchange_rate = fields.Monetary(string='Exchange rate', tracking=True)
