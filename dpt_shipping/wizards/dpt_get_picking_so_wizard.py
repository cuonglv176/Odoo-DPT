# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class DPTGetPickingSOWizard(models.TransientModel):
    _name = 'dpt.get.picking.so.wizard'

    sale_id = fields.Many2one('sale.order', 'Sale Order')
    picking_ids = fields.Many2many('stock.picking', 'Pickings',
                                   domain=[('sale_purchase_id', '=', False), ('is_main_incoming', '=', True)])

    def action_update_picking_to_so(self):
        self.picking_ids.update({
            'sale_purchase_id': self.sale_id.id
        })
