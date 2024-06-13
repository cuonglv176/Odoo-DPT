from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_id = fields.Many2one('sale.order', 'Sale')
    package_line_ids = fields.One2many('purchase.order.line.package', 'purchase_id', 'Package Line')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not self.env.context.get('create_from_so', False):
            return res
        # create ticket and auto mark done ticket
        return res
