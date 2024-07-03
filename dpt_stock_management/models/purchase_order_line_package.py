from odoo import fields, models, api, _


class PurchaseOrderLinePackage(models.Model):
    _inherit = 'purchase.order.line.package'

    move_ids = fields.One2many('stock.move', 'package_line_id', 'Move')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    product_ids = fields.Many2many('product.product', compute="_compute_product")
    created_picking_qty = fields.Integer('Quantity Created Picking', compute='compute_created_picking_qty')

    def compute_created_picking_qty(self):
        for item in self:
            out_picking_ids = self.env['stock.picking'].sudo().search([('picking_in_id', '=', item.picking_id.id)])
            out_picking_ids = out_picking_ids.filtered(
                lambda op: op.picking_type_id.code != 'incoming' or op.x_transfer_type != 'incoming')
            item.created_picking_qty = sum([package_id.quantity for package_id in out_picking_ids.package_ids.filtered(
                lambda p: p.uom_id.id == item.uom_id.id)])

    @api.depends('purchase_id', 'picking_id')
    def _compute_product(self):
        for item in self:
            product_ids = self.env['product.product']
            if item.purchase_id:
                product_ids |= item.purchase_id.order_line.mapped('product_id')
            if item.picking_id:
                product_ids |= item.picking_id.move_ids_product.mapped('product_id')
            item.product_ids = product_ids if product_ids else self.env['product.product'].search([])

    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            values.append(line._prepare_stock_moves(picking))

        return self.env['stock.move'].create(values) if values else None

    def _prepare_stock_moves(self, picking):
        date_planned = picking.date_deadline or fields.Datetime.now()
        vals = {
            'name': (self.uom_id.product_id.display_name or '')[:2000],
            'product_id': self.uom_id.product_id.id,
            'package_line_id': self.id,
            'date': date_planned,
            'date_deadline': date_planned,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': picking.partner_id.id,
            'state': 'draft',
            'company_id': picking.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'group_id': picking.group_id.id,
            'origin': picking.name,
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.product_id.uom_id.id,
            'move_line_ids': [(0, 0, {
                'company_id': self.env.company.id,
                'product_id': self.uom_id.product_id.id,
                'lot_name': self.picking_id.name,
                'quantity': self.quantity,
            })]
        }
        return vals
