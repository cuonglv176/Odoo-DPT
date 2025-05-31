# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DPTPricelistRejectWizard(models.TransientModel):
    _name = 'dpt.pricelist.reject.wizard'
    _description = 'Từ chối phê duyệt bảng giá'

    pricelist_id = fields.Many2one('product.pricelist', string='Bảng giá', required=True)
    reason = fields.Text(string='Lý do từ chối', required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.pricelist_id:
            self.pricelist_id.write({
                'state': 'rejected',
                'rejection_reason': self.reason,
            })
        return {'type': 'ir.actions.act_window_close'}