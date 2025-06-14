# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _prepare_new_lot_vals(self):
        res = super()._prepare_new_lot_vals()
        package_id = self.move_id.picking_id.package_ids.filtered(lambda pk: self.move_id.id in pk.move_ids.ids)
        if not package_id:
            return res
        res.update({
            'weight': package_id[0].weight,
            'volume': package_id[0].volume,
            'total_weight': package_id[0].total_weight,
            'total_volume': package_id[0].total_weight,
        })
        return res
