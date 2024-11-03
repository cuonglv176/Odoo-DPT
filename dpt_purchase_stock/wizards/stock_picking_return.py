# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_picking_default_values(self):
        res = super()._prepare_picking_default_values()
        package_vals = []
        for package_id in self.picking_id.package_ids:
            lot_id = self.env['stock.lot'].sudo().search(
                [('product_id', '=', package_id.uom_id.product_id.id), ('name', '=', self.picking_id.picking_lot_name)])
            if not lot_id:
                continue
            return_line_id = self.product_return_moves.filtered(lambda rl: rl.product_id.id == package_id.uom_id.product_id.id)
            if not return_line_id:
                continue
            package_vals.append((0, 0, {
                'quantity': return_line_id.quantity,
                'uom_id': package_id.uom_id.id,
                'length': package_id.length,
                'width': package_id.width,
                'height': package_id.height,
                'weight': package_id.weight,
                'volume': package_id.volume,
                'total_volume': math.ceil(round(package_id.volume * package_id.quantity * 100, 4)) / 100,
                'total_weight': math.ceil(round(package_id.weight * package_id.quantity, 2)),
                'sale_id': self.picking_id.sale_purchase_id.id,
                'lot_id': lot_id.id,
            }))
        if package_vals:
            res['package_ids'] = package_vals
        return res
