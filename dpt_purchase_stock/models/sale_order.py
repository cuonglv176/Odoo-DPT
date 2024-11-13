# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    number_main_incoming_picking = fields.Integer(string='Number Main Incoming Picking',
                                                  compute='_compute_number_picking')
    number_transfer = fields.Integer(string='Number Transfer', compute='_compute_number_picking')

    def recompute_weight_volume(self):
        all_incoming_picking_id = self.env['stock.picking'].sudo().search(
            [('sale_purchase_id', '=', self.id), ('is_main_incoming', '=', True)])
        self.with_context(onchange_sale_service_ids=True).write({
            'volume': sum(all_incoming_picking_id.mapped('total_volume')),
            'weight': sum(all_incoming_picking_id.mapped('total_weight')),
        })
        self.onchange_weight_volume()

    def _compute_number_picking(self):
        for item in self:
            item.number_main_incoming_picking = self.env['stock.picking'].sudo().search_count(
                [('sale_purchase_id', '=', item.id), ('is_main_incoming', '=', True)])
            in_out_picking_ids = self.env['stock.picking'].sudo().search(
                [('sale_purchase_id', '=', item.id),
                 ('x_transfer_type', 'in', ('outgoing_transfer', 'incoming_transfer'))])
            export_import_ids = self.env['dpt.export.import.line'].sudo().search(
                [('sale_id', '=', item.id)]).mapped('export_import_id')
            item.number_transfer = self.env['dpt.shipping.slip'].sudo().search_count(
                ['|', '|', ('export_import_ids', 'in', export_import_ids.ids),
                 ('in_picking_ids', 'in', in_out_picking_ids.ids), ('out_picking_ids', 'in', in_out_picking_ids.ids)])

    def action_show_main_incoming_picking(self):
        action = self.env.ref('stock.action_picking_tree_incoming').sudo().read()[0]
        action['domain'] = [('sale_purchase_id', '=', self.id), ('is_main_incoming', '=', True)]
        return action

    def action_show_transfer(self):
        action = self.env.ref('dpt_shipping.dpt_shipping_slip_action').sudo().read()[0]
        in_out_picking_ids = self.env['stock.picking'].sudo().search(
            [('sale_purchase_id', '=', self.id),
             ('x_transfer_type', 'in', ('outgoing_transfer', 'incoming_transfer'))])
        export_import_ids = self.env['dpt.export.import.line'].sudo().search(
            [('sale_id', '=', self.id)]).mapped('export_import_id')
        shipping_ids = self.env['dpt.shipping.slip'].sudo().search(
            ['|', '|', ('export_import_ids', 'in', export_import_ids.ids),
             ('in_picking_ids', 'in', in_out_picking_ids.ids), ('out_picking_ids', 'in', in_out_picking_ids.ids)])
        action['domain'] = [('id', 'in', shipping_ids.ids)]
        return action
