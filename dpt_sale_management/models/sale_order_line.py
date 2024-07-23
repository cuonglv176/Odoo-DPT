from odoo import models, fields, api, _
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    legal_xhd = fields.Char(string="Legel XHD")
