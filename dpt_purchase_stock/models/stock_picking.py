from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_ids = fields.One2many('purchase.order.line.package', 'picking_id', 'Packages')
