# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # using for select location in internal picking
    x_location_id = fields.Many2one('stock.location', 'Source Location', check_company=True, copy=True,
                                    default=lambda self: self.env['stock.picking.type'].browse(
                                        self._context.get('default_picking_type_id')).default_location_src_id)
    x_location_dest_id = fields.Many2one('stock.location', 'Destination Location', check_company=True, copy=True,
                                         default=lambda self: self.env['stock.picking.type'].browse(
                                             self._context.get('default_picking_type_id')).default_location_dest_id)
    x_in_transfer_picking_id = fields.Many2one('stock.picking', 'Transfer Incoming Picking', copy=False)
    x_transfer_type = fields.Selection([('outgoing_transfer', 'Outgoing'), ('incoming_transfer', 'Incoming')],
                                       string='Transfer Type', copy=False)

    @api.onchange('picking_type_id')
    def _onchange_get_transfer_type(self):
        if not self.picking_type_id or self.picking_type_id.code != 'internal':
            return
        self.x_transfer_type = 'outgoing_transfer'
        # self._onchange_get_location()

    # @api.onchange('x_location_id', 'x_location_dest_id', 'x_in_transfer_picking_id')
    # def _onchange_get_location(self):
    #     if self.picking_type_code != 'internal':
    #         return
    #     transit_location_id = self.env['stock.location'].sudo().search(
    #         [('usage', '=', 'transit'), ('company_id', '=', self.env.company.id)], limit=1)
    #     if not transit_location_id:
    #         raise ValidationError(_('Please configurate 1 Inter-warehouse Transit location'))
    #     if self.x_location_id:
    #         self.location_id = self.x_location_id if self.x_transfer_type == 'outgoing_transfer' else transit_location_id
    #     if self.x_location_dest_id:
    #         self.location_dest_id = transit_location_id if self.x_transfer_type == 'outgoing_transfer' else self.x_location_dest_id
    #     for line in self.move_line_ids_without_package:
    #         line.location_id = self.location_id
    #         line.location_dest_id = self.location_dest_id
    #     for line in self.move_ids_without_package:
    #         line.location_id = self.location_id
    #         line.location_dest_id = self.location_dest_id

    def create_in_transfer_picking(self, location_dest_id):
        # logic transfer - create incoming picking
        transit_location_id = self.env['stock.location'].sudo().search(
            [('usage', '=', 'transit'), ('company_id', '=', self.env.company.id)], limit=1)
        if not transit_location_id:
            raise ValidationError(_('Please configurate 1 Inter-warehouse Transit location'))
        if not location_dest_id:
            raise ValidationError(_('Missing another Internal Location. Please check other Internal location'))
        for picking in self:
            new_picking_type_id = self.env['stock.picking.type'].sudo().search(
                [('warehouse_id', '=', location_dest_id.warehouse_id.id), ('code', '=', 'internal')], limit=1)
            if not new_picking_type_id:
                raise ValidationError(
                    f'Vui lòng tạo loại điều chuyển cho kho {location_dest_id.warehouse_id.name}')
            in_transfer_picking_id = picking.copy({
                'location_id': transit_location_id.id,
                'location_dest_id': location_dest_id.id,
                'x_transfer_type': 'incoming_transfer',
                'origin': picking.name,
                'picking_type_id': new_picking_type_id.id,
                'picking_lot_name': picking.picking_lot_name,
                'package_ids': [(0, 0, {
                    'code': package_id.code,
                    'date': package_id.date,
                    'uom_id': package_id.uom_id.id,
                    'quantity': package_id.quantity,
                    'length': package_id.length,
                    'width': package_id.width,
                    'height': package_id.height,
                    'size': package_id.size,
                    'total_weight': math.ceil(round(package_id.weight * package_id.quantity, 2)) * (package_id.quantity - package_id.created_picking_qty) / package_id.quantity,
                    'weight': package_id.weight,
                    'volume': package_id.volume,
                    'total_volume': (math.ceil(round(package_id.volume * package_id.quantity * 100, 4)) / 100) * (package_id.quantity - package_id.created_picking_qty) / package_id.quantity,
                    'note': package_id.note,
                    'image': package_id.image,
                    'detail_ids': [(0, 0, {
                        'product_id': detail_id.product_id.id,
                        'uom_id': detail_id.uom_id.id,
                        'quantity': detail_id.quantity
                    }) for detail_id in package_id.detail_ids] if package_id.detail_ids else None,
                    # 'lot_ids': package_id.lot_ids.ids if package_id.lot_ids else None
                }) for package_id in picking.package_ids],
                # 'move_ids_without_package': [(0, 0, {
                #     'location_id': transit_location_id.id,
                #     'location_dest_id': location_dest_id.id,
                #     'name': (move_line_id.product_id.display_name or '')[:2000],
                #     'product_id': move_line_id.product_id.id,
                #     'product_uom_qty': move_line_id.product_uom_qty,
                #     'product_uom': move_line_id.product_uom.id,
                # }) for move_line_id in picking.move_ids_without_package],
            })
            in_transfer_picking_id.move_ids_without_package.write({
                'location_id': transit_location_id.id,
                'location_dest_id': location_dest_id.id,
            })
            picking.x_in_transfer_picking_id = in_transfer_picking_id.id
            in_transfer_picking_id.action_update_picking_name()
            move_line_vals = []
            in_transfer_picking_id.move_line_ids.unlink()
            for move_id in in_transfer_picking_id.move_ids_without_package.filtered(lambda m: not m.move_line_ids):
                lot_id = self.env['stock.lot'].search(
                    [('product_id', '=', move_id.product_id.id), ('name', '=', picking.picking_in_id.picking_lot_name)],
                    limit=1)
                move_line_vals.append({
                    'picking_id': in_transfer_picking_id.id,
                    'move_id': move_id.id,
                    'lot_id': lot_id.id,
                    'location_id': move_id.location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_uom_qty,
                    'product_uom_id': move_id.product_uom.id,
                })
                if move_line_vals:
                    self.env['stock.move.line'].create(move_line_vals)
            # in_transfer_picking_id._onchange_get_location()
            # in_transfer_picking_id.action_confirm()
