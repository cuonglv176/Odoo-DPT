from odoo import models, fields, api, _


class SaleOrderField(models.Model):
    _inherit = 'dpt.sale.order.fields'

    picking_id = fields.Many2one('stock.picking', string='Picking')
