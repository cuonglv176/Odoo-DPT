from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_purchase_id = fields.Many2one(related="purchase_id.sale_id")
