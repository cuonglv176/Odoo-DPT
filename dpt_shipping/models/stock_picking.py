# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    valid_cutlist = fields.Boolean('Valid Cutlist', compute="_compute_valid_cutlist", store=True)

    def cron_update_valid_cutlist_picking(self):
        picking_ids = self.env['stock.picking'].sudo().search([])
        picking_ids._compute_valid_cutlist()

    @api.depends('sale_purchase_id', 'state', 'sale_purchase_id.ticket_ids', 'sale_purchase_id.dpt_export_import_ids')
    def _compute_valid_cutlist(self):
        # đã nhập đủ kiện, sản phẩm
        # đủ khai báo XNK
        # các ticket ở kho TQ đều hoàn thành
        for item in self:
            valid_cutlist = False
            if item.state not in ('done', 'cancel') and item.picking_type_code == 'incoming' and (item.x_transfer_type == 'outgoing_transfer' and item.location_id.warehouse_id.is_main_incoming_warehouse) and item.sale_purchase_id and all(
                    [ticket_id.stage_id.is_done_stage for ticket_id in item.sale_purchase_id.ticket_ids if
                     ticket_id.department_id.is_chinese_stock_department]) and item.sale_purchase_id.dpt_export_import_ids:
                valid_cutlist = True
            item.valid_cutlist = valid_cutlist

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._compute_valid_cutlist()
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'valid_cutlist' in vals:
            return res
        for item in self:
            item._compute_valid_cutlist()
        return res

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
