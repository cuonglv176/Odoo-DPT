from odoo import fields, models, api, _


class PurchaseOrderLinePackageDetail(models.Model):
    _name = 'purchase.order.line.package.detail'
    _description = 'Purchase Package Detail'

    sequence = fields.Integer(default=1)
    product_id = fields.Many2one('product.product', 'Product')
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    uom_id = fields.Many2one('uom.uom', 'Unit')
    quantity = fields.Float('Quantity')
    package_id = fields.Many2one('purchase.order.line.package', 'Package')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            product_in_po_line_id = self.package_id.purchase_id.order_line.filtered(
                lambda pol: pol.product_template_id == self.product_id.product_tmpl_id)
            if product_in_po_line_id:
                self.uom_id = product_in_po_line_id.uom_id
