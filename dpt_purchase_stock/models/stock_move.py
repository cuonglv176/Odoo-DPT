# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    package_line_id = fields.Many2one('purchase.order.line.package', 'Package Line')
