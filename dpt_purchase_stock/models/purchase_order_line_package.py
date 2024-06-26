from odoo import fields, models, api, _


class PurchaseOrderLinePackage(models.Model):
    _inherit = 'purchase.order.line.package'

    move_ids = fields.One2many('stock.move', 'package_line_id', 'Move')
    picking_id = fields.Many2one('stock.picking', 'Picking')

    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)

        return self.env['stock.move'].create(values) if values else None

    def _prepare_stock_moves(self, picking):
        date_planned = picking.date_deadline
        if self.purchase_id:
            lot_name = self.purchase_id.packing_lot_name + f'_{self.quantity}{self.uom_id.packing_code}'
        else:
            lot_name = self.picking_id.name + f'_{self.quantity}{self.uom_id.packing_code}'
        return [{
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
            'purchase_line_id': self.id,
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
                'lot_name': lot_name,
                'quantity': self.quantity,
            })]
        }]
