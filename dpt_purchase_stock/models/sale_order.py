# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def recompute_weight_volume(self):
        all_incoming_picking_id = self.env['stock.picking'].sudo().search(
            [('sale_purchase_id', '=', self.id), ('is_main_incoming', '=', True)])
        self.with_context(onchange_sale_service_ids=True).write({
            'volume': sum(all_incoming_picking_id.mapped('total_volume')),
            'weight': sum(all_incoming_picking_id.mapped('total_weight')),
        })
        self.onchange_weight_volume()
