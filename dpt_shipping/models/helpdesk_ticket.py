# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' not in vals:
            return res
        for rec in self:
            if not rec.stage_id.is_done_stage or not rec.department_id.is_chinese_stock_department:
                continue
            picking_ids = self.env['stock.picking'].sudo().search(
                [('sale_purchase_id', '=', rec.sale_id.id), ('state', '=', 'done'),
                 ('is_main_incoming', '=', True)])
            picking_ids._compute_valid_cutlist()
        return res

    def _compute_display_name(self):
        for rec in self:
            name = f"{rec.partner_id.name if rec.partner_id else ''}-{rec.sale_id.name if rec.sale_id else ''}"
            picking_id = self.env['stock.picking'].sudo().search(
                [('sale_purchase_id', '=', rec.sale_id.id), ('state', '=', 'done'),
                 ('is_main_incoming', '=', True)], order="id desc", limit=1)
            if picking_id:
                name += f"-{picking_id.picking_lot_name if picking_id else ''}-{picking_id.packing_lot_name if picking_id else ''}"
            rec.display_name = name + f"-{rec.name}"
