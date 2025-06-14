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

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if self.env.context.get('show_in_quant', False):
            picking_ids = self.env['stock.picking'].sudo().search(
                ['|', ('picking_lot_name', operator, name), ('packing_lot_name', operator, name)])
            sale_ids = picking_ids.mapped('sale_purchase_id')
            if sale_ids:
                domain = ['|', '|', '|', ('partner_id.name', operator, name), ('sale_id.name', operator, name),
                          ('sale_id', 'in', sale_ids.ids), ('name', operator, name)]
            else:
                domain = ['|', '|', ('partner_id.name', operator, name), ('sale_id.name', operator, name),
                          ('name', operator, name)]
        return self._search(domain, limit=limit, order=order)
