# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_update_picking(self):
        action = self.env.ref('dpt_shipping.dpt_get_picking_so_wizard_action').sudo().read()[0]
        picking_type_id = self.env['stock.picking.type'].sudo().search(
            [('code', '=', 'incoming'), ('warehouse_id.is_main_incoming_warehouse', '=', True)], limit=1)
        action['context'] = {'default_sale_id': self.id, 'default_picking_type_id': picking_type_id.id}
        return action
