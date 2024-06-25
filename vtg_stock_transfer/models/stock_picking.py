# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # using for select location in internal picking
    x_location_id = fields.Many2one('stock.location', 'Source Location', check_company=True,
                                    states={'draft': [('readonly', False)]},
                                    default=lambda self: self.env['stock.picking.type'].browse(
                                        self._context.get('default_picking_type_id')).default_location_src_id)
    x_location_dest_id = fields.Many2one('stock.location', 'Destination Location', check_company=True,
                                         states={'draft': [('readonly', False)]},
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
        self._onchange_get_location()

    @api.onchange('x_location_id', 'x_location_dest_id', 'x_in_transfer_picking_id')
    def _onchange_get_location(self):
        if self.picking_type_code != 'internal':
            return
        transit_location_id = self.env['stock.location'].sudo().search(
            [('usage', '=', 'transit'), ('company_id', '=', self.env.company.id)], limit=1)
        if not transit_location_id:
            raise ValidationError(_('Please configurate 1 Inter-warehouse Transit location'))
        if self.x_location_id:
            self.location_id = self.x_location_id if self.x_transfer_type == 'outgoing_transfer' else transit_location_id
        if self.x_location_dest_id:
            self.location_dest_id = transit_location_id if self.x_transfer_type == 'outgoing_transfer' else self.x_location_dest_id
        for line in self.move_line_ids_without_package:
            line.location_id = self.location_id
            line.location_dest_id = self.location_dest_id

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        for picking in res:
            if picking.x_transfer_type != 'outgoing_transfer':
                continue
            picking.create_in_transfer_picking()
        return res

    def create_in_transfer_picking(self):
        # logic transfer - create incoming picking
        transit_location_id = self.env['stock.location'].sudo().search(
            [('usage', '=', 'transit'), ('company_id', '=', self.env.company.id)], limit=1)
        if not transit_location_id:
            raise ValidationError(_('Please configurate 1 Inter-warehouse Transit location'))
        for picking in self:
            new_picking_type_id = self.env['stock.picking.type'].sudo().search(
                [('warehouse_id', '=', picking.x_location_dest_id.warehouse_id.id), ('code', '=', 'internal')], limit=1)
            if not new_picking_type_id:
                raise ValidationError(f'Vui lòng tạo loại điều chuyển cho kho {picking.x_location_dest_id.warehouse_id.name}')
            in_transfer_picking_id = picking.copy({
                'x_location_id': picking.x_location_id.id,
                'x_location_dest_id': picking.x_location_dest_id.id,
                'location_id': transit_location_id.id,
                'location_dest_id': picking.x_location_dest_id.id,
                'x_transfer_type': 'incoming_transfer',
                'origin': picking.name,
                'picking_type_id': new_picking_type_id.id,
            })
            in_transfer_picking_id._onchange_get_location()
            # in_transfer_picking_id.action_confirm()
            picking.x_in_transfer_picking_id = in_transfer_picking_id.id
