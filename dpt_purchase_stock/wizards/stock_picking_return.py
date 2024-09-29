# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_picking_default_values(self):
        res = super()._prepare_picking_default_values()
        package_vals = []
        for package_id in self.picking_id.package_ids:
            lot_id = package_id.lot_id
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
                'total_volume': package_id.total_volume,
                'total_weight': package_id.total_weight,
                'sale_id': package_id.sale_purchase_id.id,
                'lot_id': lot_id.id,
            }))
        if package_vals:
            res['package_id'] = package_vals
        return res
