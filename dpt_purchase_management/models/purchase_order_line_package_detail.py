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
    product_ids = fields.Many2many('product.product', compute="_compute_product")

    def _compute_product(self):
        for item in self:
            product_ids = self.env['product.product']
            if item.package_id.purchase_id:
                product_ids |= item.package_id.purchase_id.order_line.mapped('product_id')
            if item.package_id.picking_id:
                product_ids |= item.package_id.picking_id.move_ids_product.mapped('product_id')
            item.product_ids = product_ids if product_ids else self.env['product.product'].search([])

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            product_in_po_line_id = self.package_id.purchase_id.order_line.filtered(
                lambda pol: pol.product_id == self.product_id)
            if product_in_po_line_id:
                self.uom_id = product_in_po_line_id.uom_id

    @api.onchange('sale_line_id')
    def onchange_sale_line(self):
        if self.sale_line_id:
            self.uom_id = self.sale_line_id.uom_id
            self.product_id = self.sale_line_id.product_id
