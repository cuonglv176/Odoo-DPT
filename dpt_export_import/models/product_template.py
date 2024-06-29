# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import collections
from datetime import timedelta
from itertools import groupby
import operator as py_operator
from odoo import fields, models, _
from odoo.tools import groupby
from odoo.tools.float_utils import float_round, float_is_zero


class ProductTemplate(models.Model):
    _inherit = "product.template"

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
    hs_code_id = fields.Many2one('dpt.export.import.acfta', string='HS Code')
    dpt_code_hs = fields.Char(string='H')
    dpt_sl1 = fields.Integer(string='SL1', tracking=True)
    dpt_uom1_id = fields.Many2one('uom.uom', string='ĐVT 1', tracking=True)
    dpt_sl2 = fields.Integer(string='SL2', tracking=True)
    dpt_export_import_line_ids = fields.One2many('dpt.export.import.line', 'product_tmpl_id', string='Declaration line')
