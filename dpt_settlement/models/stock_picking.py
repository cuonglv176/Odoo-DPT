# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_id = fields.Many2one('account.payment', 'Payment')
