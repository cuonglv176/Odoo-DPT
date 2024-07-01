# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_code = fields.Char('Transfer Code')
    transfer_code_chinese = fields.Char('Transfer Code in Chinese')
    package_ids = fields.One2many('purchase.order.line.package', 'picking_id', 'Packages')
    move_ids_product = fields.One2many('stock.move', 'picking_id', string="Stock move",
                                       domain=[('is_package', '=', False)], copy=False)
    picking_in_id = fields.Many2one('stock.picking', 'Picking In')
    picking_out_ids = fields.One2many('stock.picking', 'picking_in_id', 'Picking Out')
    num_picking_out = fields.Integer('Num Picking Out', compute="_compute_num_picking_out")
    finish_create_picking = fields.Boolean('Finish Create Picking', compute="_compute_finish_create_picking")
    packing_lot_name = fields.Char('Packing Lot name', compute="compute_packing_lot_name", store=True)

    @api.depends('package_ids.quantity', 'package_ids.uom_id.packing_code')
    def compute_packing_lot_name(self):
        for item in self:
            item.packing_lot_name = '.'.join(
                [f"{package_line_id.quantity}{package_line_id.uom_id.packing_code}" for package_line_id in
                 item.package_ids if package_line_id.uom_id.packing_code])

    def _compute_num_picking_out(self):
        for item in self:
            item.num_picking_out = len(item.picking_out_ids)

    def _compute_finish_create_picking(self):
        for item in self:
            item.finish_create_picking = all(
                [package_id.quantity == package_id.created_picking_qty for package_id in item.package_ids])

    def create(self, vals):
        res = super().create(vals)
        # getname if it is incoming picking in Chinese stock
        if res.picking_type_code == 'incoming' and res.location_dest_id.warehouse_id.is_main_incoming_warehouse:
            prefix = f'KT{datetime.now().strftime("%y%m%d")}'
            nearest_picking_id = self.env['stock.picking'].sudo().search(
                [('name', 'ilike', prefix + "%"), ('id', '!=', res.id), ('warehouse_id', '=', res.warehouse_id.id),
                 ('picking_type_id.code', '=', res.picking_type_code)], order='id desc').filtered(
                lambda sp: '.' not in sp.name)
            if nearest_picking_id:
                try:
                    number = int(nearest_picking_id.name[7:])
                except:
                    number = 0
                res.name = prefix + str(number).zfill(3)
            else:
                res.name = prefix + '001'
        else:
            pass
        return res

    def action_create_transfer_picking(self):
        # condition cutlift
        other_warehouse_id = self.env['stock.warehouse'].sudo().search(
            [('id', '!=', self.location_dest_id.warehouse_id.id)], limit=1)
        if not other_warehouse_id:
            return
        picking_type_id = self.env['stock.picking.type'].sudo().search(
            [('warehouse_id', '=', other_warehouse_id.id), ('code', '=', 'internal')])
        if not picking_type_id:
            return
        transit_location_id = self.env['stock.location'].sudo().search(
            [('usage', '=', 'transit'), ('company_id', '=', self.env.company.id)], limit=1)
        return {
            'name': _('Create Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'target': 'new',
            'view_mode': 'form',
            'views': [(self.env.ref('stock.view_picking_form').sudo().id, "form")],
            'context': {
                'default_picking_in_id': self.id,
                'default_x_location_id': self.location_dest_id.id,
                'default_x_location_dest_id': other_warehouse_id.lot_stock_id.id,
                'default_picking_type_id': picking_type_id.id,
                'default_x_transfer_type': 'outgoing_transfer',
                'default_move_ids_without_package': [(0, 0, {
                    'location_id': self.location_dest_id.id,
                    'location_dest_id': transit_location_id.id,
                    'name': (move_line_id.product_id.display_name or '')[:2000],
                    'product_id': move_line_id.product_id.id,
                    'product_uom_qty': move_line_id.product_uom_qty,
                    'product_uom': move_line_id.product_uom.id,
                }) for move_line_id in self.move_ids_without_package],
                'default_package_ids': [(0, 0, {
                    'quantity': package_id.quantity - package_id.created_picking_qty,
                    'size': package_id.size,
                    'weight': package_id.weight,
                    'volume': package_id.volume,
                    'uom_id': package_id.uom_id.id,
                    'detail_ids': [(0, 0, {
                        'product_id': detail_id.product_id.id,
                        'uom_id': detail_id.uom_id.id,
                        'quantity': detail_id.quantity,
                    }) for detail_id in package_id.detail_ids],
                }) for package_id in self.package_ids if package_id.quantity - package_id.created_picking_qty != 0]
            }
        }

    def action_view_picking_out(self):
        view_id = self.env.ref('stock.vpicktree').id
        view_form_id = self.env.ref('stock.view_picking_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': _('Deposit'),
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_out_ids.ids)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }
