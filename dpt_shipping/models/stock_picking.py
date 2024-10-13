# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


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

    @api.depends('main_incoming_shipping_ids')
    def _compute_shipping_name(self):
        for item in self:
            item.shipping_name = ','.join(item.main_incoming_shipping_ids.mapped('name'))

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
