# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import math
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    in_draft_shipping = fields.Boolean('In Draft Shipping', compute="_compute_in_draft_shipping",
                                       search="_search_in_draft_shipping")
    finish_stock_services = fields.Boolean('Finish Stock Services', compute="_compute_valid_cutlist", store=True)
    have_stock_label = fields.Boolean('Have Stock Labels', compute="_compute_valid_cutlist", store=True)
    have_export_import = fields.Boolean('Have Export Import', compute="_compute_valid_cutlist", store=True)
    out_shipping_ids = fields.Many2many('dpt.shipping.slip', 'stock_picking_out_shipping_rel', 'picking_id',
                                        'shipping_slip_id', string='Out Shipping')
    in_shipping_ids = fields.Many2many('dpt.shipping.slip', 'stock_picking_in_shipping_rel', 'picking_id',
                                       'shipping_slip_id', string='In Shipping')
    main_incoming_shipping_ids = fields.Many2many('dpt.shipping.slip', 'stock_picking_main_incoming_shipping_rel',
                                                  'picking_id', 'shipping_slip_id', string='Main Incoming Shipping')
    estimate_arrival_warehouse_vn = fields.Date('Estimate Arrival Warehouse VN')

    employee_sale = fields.Many2one('hr.employee', string='Employee Sale', related='sale_purchase_id.employee_sale')
    employee_cs = fields.Many2one('hr.employee', string='Employee CS', related='sale_purchase_id.employee_sale')
    shipping_name = fields.Char('Phiếu vận chuyển', compute='_compute_shipping_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    is_return_related = fields.Boolean('Is Return', compute="_compute_is_return_related",
                                       search="_search_is_return_related")

    total_left_quantity = fields.Float(compute='_compute_total_quantity')
    total_transfer_quantity = fields.Float(compute='_compute_total_quantity')

    def _compute_total_quantity(self):
        for item in self:
            item.total_left_quantity = sum(item.package_ids.mapped('quantity')) - sum(
                item.package_ids.mapped('transferred_quantity'))
            item.total_transfer_quantity = sum(item.package_ids.mapped('transfer_quantity'))

    @api.depends('return_id')
    def _compute_is_return_related(self):
        for item in self:
            if item.return_id:
                item.is_return_related = True
            else:
                return_picking_count = self.env['stock.picking'].sudo().search_count([('return_id', '=', item.id)])
                item.is_return_related = True if return_picking_count else False

    def _search_is_return_related(self, operator, value):
        have_return_picking_ids = self.env['stock.picking'].sudo().search([('return_id', '!=', False)])
        all_picking_ids = have_return_picking_ids | have_return_picking_ids.mapped('return_id')
        # case False
        if (operator == '!=' and value) or (operator == '=' and not value):
            return [('id', 'not in', all_picking_ids.ids)]
        else:
            return [('id', 'in', all_picking_ids.ids)]

    @api.depends('main_incoming_shipping_ids', 'main_incoming_shipping_ids.name',
                 'main_incoming_shipping_ids.vehicle_country')
    def _compute_shipping_name(self):
        for item in self:
            shipping_name = []
            for shipping_id in item.main_incoming_shipping_ids.filtered(lambda sh: sh.vehicle_country == 'chinese'):
                if shipping_id.name:
                    shipping_name.append(shipping_id.name)
            item.shipping_name = ','.join(shipping_name) if shipping_name else None

    def _compute_in_draft_shipping(self):
        for item in self:
            draft_shipping_slip_ids = self.env['dpt.shipping.slip'].sudo().search(
                ['|', ('out_picking_ids', 'in', [item.id]), ('in_picking_ids', 'in', [item.id]), '|', '&',
                 ('vehicle_country', '=', 'chinese'), ('cn_vehicle_stage_id.is_draft_stage', '=', True), '&',
                 ('vehicle_country', '=', 'vietnamese'), ('vn_vehicle_stage_id.is_draft_stage', '=', True)])
            item.in_draft_shipping = True if draft_shipping_slip_ids else False

    def _search_in_draft_shipping(self, operator, value):
        draft_shipping_slip_ids = self.env['dpt.shipping.slip'].sudo().search(
            ['|', '&', ('vehicle_country', '=', 'chinese'), ('cn_vehicle_stage_id.is_draft_stage', '=', True), '&',
             ('vehicle_country', '=', 'vietnamese'), ('vn_vehicle_stage_id.is_draft_stage', '=', True)])
        picking_ids = draft_shipping_slip_ids.out_picking_ids | draft_shipping_slip_ids.in_picking_ids
        if (operator == '!=' and value) or (operator == '==' and not value):
            return [('id', 'not in', picking_ids.ids)]
        else:
            return [('id', 'in', picking_ids.ids)]

    def cron_update_valid_cutlist_picking(self):
        picking_ids = self.env['stock.picking'].sudo().search([])
        picking_ids._compute_valid_cutlist()

    @api.depends('sale_purchase_id', 'state', 'sale_purchase_id.ticket_ids', 'sale_purchase_id.dpt_export_import_ids',
                 'exported_label', 'sale_purchase_id.dpt_export_import_line_ids')
    def _compute_valid_cutlist(self):
        # đã nhập đủ kiện, sản phẩm
        # đủ khai báo XNK
        # các ticket ở kho TQ đều hoàn thành
        for item in self:
            item.finish_stock_services = item.sale_purchase_id and (all(
                [ticket_id.stage_id.is_done_stage for ticket_id in item.sale_purchase_id.ticket_ids if
                 ticket_id.department_id.is_chinese_stock_department]) or not item.sale_purchase_id.ticket_ids.filtered(
                lambda t: t.department_id.is_chinese_stock_department))
            item.have_stock_label = item.exported_label
            dpt_export_import_line_ids = self.env['dpt.export.import.line'].sudo().search(
                [('stock_picking_ids', 'in', [item.id]),
                 ('state', 'in', ['eligible', 'declared', 'released', 'consulted', 'post_control'])])
            item.have_export_import = True if (
                                                      item.sale_purchase_id and item.sale_purchase_id.dpt_export_import_line_ids.filtered(
                                                  lambda eil: eil.state in ['eligible', 'declared', 'released',
                                                                            'consulted',
                                                                            'post_control'])) or dpt_export_import_line_ids else False

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not ('finish_stock_services' in vals or 'have_stock_label' in vals or 'have_export_import' in vals):
            res._compute_valid_cutlist()
        if res.x_transfer_type == 'outgoing_transfer' and res.picking_in_id:
            shipping_slip_ids = self.env['dpt.shipping.slip'].sudo().search(
                [('main_in_picking_ids', 'in', res.picking_in_id.ids)])
            if shipping_slip_ids:
                shipping_slip_ids.out_picking_ids = shipping_slip_ids.out_picking_ids | res
        return res

    def write(self, vals):
        res = super().write(vals)
        for item in self:
            if not ('finish_stock_services' in vals or 'have_stock_label' in vals or 'have_export_import' in vals):
                item._compute_valid_cutlist()
            # update shipping split
            item.update_shipping_split()
        return res

    def update_shipping_split(self):
        shipping_slip_id = self.env['dpt.shipping.slip'].sudo().search(
            ['|', ('out_picking_ids', 'in', self.ids), ('in_picking_ids', 'in', self.ids)], limit=1)
        if not shipping_slip_id:
            return
        if shipping_slip_id.vehicle_country == 'chinese':
            invalid_picking_ids = shipping_slip_id.out_picking_ids.filtered(
                lambda sp: not sp.finish_stock_services or not sp.have_stock_label or not sp.have_export_import)
        elif shipping_slip_id.vehicle_country == 'vietnamese':
            invalid_picking_ids = shipping_slip_id.in_picking_ids.filtered(
                lambda sp: not sp.finish_stock_services or not sp.have_stock_label or not sp.have_export_import)
        else:
            return
        if not invalid_picking_ids:
            ready_stage_id = self.env['dpt.vehicle.stage'].sudo().search(
                [('country', '=', shipping_slip_id.vehicle_country), ('is_ready_stage', '=', True)], limit=1,
                order="id")
            if ready_stage_id:
                if shipping_slip_id.vehicle_country == 'chinese':
                    shipping_slip_id.cn_vehicle_stage_id = ready_stage_id
                elif shipping_slip_id.vehicle_country == 'vietnamese':
                    shipping_slip_id.vn_vehicle_stage_id = ready_stage_id

    def action_create_shipping_slip(self):
        default_vehicle_stage_id = self.env['dpt.vehicle.stage'].sudo().search([('is_default', '=', True)], limit=1)
        sale_ids = self.mapped('sale_purchase_id')
        shipping_slip_id = self.env['dpt.shipping.slip'].create({
            'sale_ids': sale_ids.ids,
            'picking_ids': self.ids,
            'vehicle_stage_id': default_vehicle_stage_id.id if default_vehicle_stage_id else None,
        })
        action = self.env.ref('dpt_shipping.dpt_shipping_slip_action').sudo().read()[0]
        action['domain'] = [('id', '=', shipping_slip_id.id)]
        py_ctx = json.loads(action.get('context', {}))
        py_ctx['create'] = 0
        py_ctx['delete'] = 0
        action['context'] = py_ctx
        return action

    def action_update_transfer_quantity(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': _('Confirm Transfer Quantity'),
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'views': [[self.env.ref('dpt_shipping.dpt_stock_picking_shipping_form_view').id, 'form']],
        }

    # re-define
    def create_in_transfer_picking(self, transit_location_id=None, location_dest_id=None):
        # logic transfer - create incoming picking
        if not transit_location_id:
            transit_location_id = self.env['stock.location'].sudo().search(
                [('usage', '=', 'internal'), ('warehouse_id.is_vn_transit_warehouse', '=', True)], limit=1)

        if not transit_location_id:
            raise ValidationError("Vui lòng kiểm tra lại kho chuyển phía Việt Nam")
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
                    'quantity': package_id.transfer_quantity,
                    'transfer_quantity': package_id.transfer_quantity,
                    'length': package_id.length,
                    'width': package_id.width,
                    'height': package_id.height,
                    'size': package_id.size,
                    'total_weight': math.ceil(round(package_id.weight * package_id.transfer_quantity, 2)) * (
                            package_id.transfer_quantity - package_id.created_picking_qty) / package_id.transfer_quantity,
                    'weight': package_id.weight,
                    'volume': package_id.volume,
                    'total_volume': (math.ceil(
                        round(package_id.volume * package_id.transfer_quantity * 100, 4)) / 100) * (
                                            package_id.transfer_quantity - package_id.created_picking_qty) / package_id.transfer_quantity,
                    'note': package_id.note,
                    'image': package_id.image,
                    'detail_ids': [(0, 0, {
                        'product_id': detail_id.product_id.id,
                        'uom_id': detail_id.uom_id.id,
                        'quantity': detail_id.transfer_quantity
                    }) for detail_id in package_id.detail_ids] if package_id.detail_ids else None,
                }) for package_id in picking.package_ids if package_id.transfer_quantity],
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

            # update transferred quantity
            for package_id in picking.package_ids:
                package_id.transferred_quantity = package_id.transferred_quantity + package_id.transfer_quantity

            if self.env.context.get('confirm_immediately'):
                in_transfer_picking_id.action_confirm()
                in_transfer_picking_id.button_validate()
