from odoo import models, fields, api, _
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    legal_xhd = fields.Char(string="Legel XHD")

    @api.model
    def create(self, vals_list):
        res = super(SaleOrderLine, self).create(vals_list)
        res.order_id.onchange_calculation_tax()
        return res

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        if self.order_id.state != 'sale':
            self.order_id.onchange_calculation_tax()
        return res
