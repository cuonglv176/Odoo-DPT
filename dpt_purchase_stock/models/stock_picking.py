import math
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_purchase_id = fields.Many2one('sale.order', 'Sale', compute="_compute_sale", inverse="_inverse_sale",
                                       store=True, copy=True)
    customer_id = fields.Many2one(related="sale_purchase_id.partner_id", string="Customer")

    outgoing_sale_ids = fields.Many2many('sale.order', 'outgoing_stock_picking_sale_order_rel', 'picking_id',
                                         'sale_id', string='Sale Orders')

    @api.depends('purchase_id', 'purchase_id.sale_id')
    def _compute_sale(self):
        for item in self:
            item.sale_id = item.purchase_id.sale_id

    def _inverse_sale(self):
        pass

    def _sanity_check(self, separate_pickings=True):
        pass

    @api.constrains('sale_purchase_id', 'package_ids', 'package_ids.total_weight', 'package_ids.total_volume',
                    'total_volume', 'total_weight')
    def constrains_picking(self):
        for item in self:
            if not item.sale_purchase_id:
                continue
            item.sale_purchase_id.recompute_weight_volume()

    def write(self, vals):
        old_sale_purchase_id = self.sale_purchase_id
        res = super().write(vals)
        if 'sale_purchase_id' in vals:
            old_sale_purchase_id.recompute_weight_volume()
        return res

    @api.onchange('outgoing_sale_ids')
    def onchange_get_detail(self):
        if not self.location_id.warehouse_id.is_main_incoming_warehouse and self.location_id.usage == 'internal' and self.picking_type_code == 'outgoing' and self.outgoing_sale_ids:
            incoming_picking_ids = self.env['stock.picking'].sudo().search(
                [('sale_purchase_id', 'in', self.outgoing_sale_ids.ids), ('location_dest_id', '=', self.location_id.id),
                 ('state', '=', 'done')])
            self.package_ids = None
            self.move_ids_without_package = None
            package_vals = []
            move_vals = []
            for picking_id in incoming_picking_ids:
                for package_id in picking_id.package_ids:
                    lot_id = self.env['stock.lot'].sudo().search(
                        [('location_id', '=', self.location_id.id), ('name', '=', picking_id.picking_lot_name),
                         ('product_id', '=', package_id.uom_id.product_id.id)], limit=1)
                    if not lot_id:
                        continue
                    package_vals.append((0, 0, {
                        'quantity': lot_id.product_qty,
                        'uom_id': package_id.uom_id.id,
                        'length': package_id.length,
                        'width': package_id.width,
                        'height': package_id.height,
                        'weight': package_id.weight,
                        'volume': package_id.volume,
                        'total_volume': math.ceil(round(package_id.volume * package_id.quantity * 100, 4)) / 100,
                        'total_weight': math.ceil(round(package_id.weight * package_id.quantity, 2)),
                        'sale_id': picking_id.sale_purchase_id.id,
                        'lot_id': lot_id.id,
                    }))
                    move_vals.append((0, 0, {
                        'from_picking_id': picking_id.id,
                        'product_id': package_id.uom_id.product_id.id,
                        'product_uom_qty': lot_id.product_qty,
                        'product_uom': package_id.uom_id.product_id.uom_id.id,
                        'partner_id': self.partner_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'name': (package_id.uom_id.product_id.display_name or '')[:2000],
                    }))
            self.package_ids = package_vals
            self.move_ids_without_package = move_vals
        else:
            self.package_ids = None
            self.move_ids_without_package = None

    @api.onchange('partner_id')
    def onchange_partner_outgoing_picking(self):
        if not self.location_id.warehouse_id.is_main_incoming_warehouse and self.location_id.usage == 'internal' and self.picking_type_code == 'outgoing' and self.partner_id:
            sale_order_ids = self.env['sale.order'].sudo().search(
                [('state', '=', 'sale'), ('partner_id', '=', self.partner_id.id)])
            self.outgoing_sale_ids = sale_order_ids
        else:
            self.outgoing_sale_ids = None
