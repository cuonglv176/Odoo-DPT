from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_ids = fields.One2many('purchase.order.line.package', 'picking_id', 'Packages')
    move_ids_product = fields.One2many('stock.move', 'picking_id', string="Stock move",
                                       domain=[('is_package', '=', False)])
    sale_purchase_id = fields.Many2one(related="purchase_id.sale_id")

    def create(self, vals):
        res = super().create(vals)
        res.onchange_package()
        return res

    @api.onchange('package_ids')
    def onchange_package(self):
        if not self._origin.id:
            return
        # remove package move
        package_move_ids = self.move_ids_without_package - self.move_ids_product
        package_move_ids.unlink()
        if self.purchase_id:
            self.package_ids.update({
                'purchase_id': self.purchase_id.id
            })
        # create package move
        self.package_ids._create_stock_moves(self)
