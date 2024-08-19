# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    service_line_ids = fields.Many2many('dpt.sale.service.management', string='Service Line')
    order_line_ids = fields.Many2many('sale.order.line', string='Order Line')
