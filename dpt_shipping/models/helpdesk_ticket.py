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
