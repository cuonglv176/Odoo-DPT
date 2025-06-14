# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    combo_id = fields.Many2one('dpt.sale.order.service.combo', string='Service Combo', 
                              help='Service combo related to this invoice line')