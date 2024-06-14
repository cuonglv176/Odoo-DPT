from odoo import fields, models, api, _


class PurchaseOrderLinePackage(models.Model):
    _inherit = 'purchase.order.line.package'

    move_ids = fields.One2many('stock.move', 'package_line_id', 'Move')

    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)

        return self.env['stock.move'].create(values)

    def _prepare_stock_moves(self, picking):
        date_planned = self.purchase_id.date_planned
        return [{
            'name': (self.uom_id.product_id.display_name or '')[:2000],
            'product_id': self.uom_id.product_id.id,
            'package_line_id': self.id,
            'date': date_planned,
            'date_deadline': date_planned,
            'location_id': self.purchase_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.purchase_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.purchase_id.dest_address_id.id,
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.purchase_id.company_id.id,
            'picking_type_id': self.purchase_id.picking_type_id.id,
            'group_id': self.purchase_id.group_id.id,
            'origin': self.purchase_id.name,
            'description_picking': self.lot_name,
            'warehouse_id': self.purchase_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.product_id.uom_id.id,
            'move_line_ids': [(0, 0, {
                'company_id': self.env.company.id,
                'product_id': self.uom_id.product_id.id,
                'lot_name': self.purchase_id.name + self.lot_name,
                'quantity': self.quantity,
            })]
        }]
