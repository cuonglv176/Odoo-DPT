# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    valid_cutlist = fields.Boolean('Valid Cutlist', compute="_compute_valid_cutlist", store=True)

    def _compute_valid_cutlist(self):
        # đã nhập đủ kiện, sản phẩm
        # đủ khai báo XNK
        for item in self:
            item.valid_cutlist = True

    def action_create_shipping_slip(self):
        default_vehicle_stage_id = self.env['dpt.vehicle.stage'].sudo().search([('is_default', '=', True)], limit=1)
        picking_ids = self.env['stock.picking'].sudo().search(
            [('sale_id', 'in', self.ids), ('x_transfer_type', '=', 'outgoing_transfer')])
        shipping_slip_id = self.env['dpt.shipping.slip'].create({
            'sale_ids': self.ids,
            'picking_ids': picking_ids.ids,
            'vehicle_stage_id': default_vehicle_stage_id.id if default_vehicle_stage_id else None,
        })
        action = self.env.ref('dpt_shipping.dpt_shipping_slip_action').sudo().read()[0]
        action['domain'] = [('id', '=', shipping_slip_id.id)]
        py_ctx = json.loads(action.get('context', {}))
        py_ctx['create'] = 0
        py_ctx['delete'] = 0
        action['context'] = py_ctx
        return action
