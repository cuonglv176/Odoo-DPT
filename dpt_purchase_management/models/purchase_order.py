from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_id = fields.Many2one('sale.order', 'Sale')
    package_line_ids = fields.One2many('purchase.order.line.package', 'purchase_id', 'Package Line')
