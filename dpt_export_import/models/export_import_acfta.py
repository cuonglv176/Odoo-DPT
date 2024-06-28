# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api

class DptExportImportACFTA(models.Model):
    _name = "dpt.export.import.acfta"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import ACFTA'

    dpt_v = fields.Integer(string='V')
    dpt_hs_code = fields.Char(string='HS Code')
    dpt_nk_tt = fields.Integer(string='NK TT')
    dpt_nk_ud = fields.Integer(string='NK ưu đãi')
    dpt_vat = fields.Integer(string='VAT')
    dpt_acfta = fields.Integer(string='ACFTA')
