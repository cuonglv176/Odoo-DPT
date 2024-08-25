# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class DPTShippingSplitWizard(models.TransientModel):
    _name = 'dpt.picking.confirm.wizard'

    available_picking_ids = fields.Many2many('sale.order', 'dpt_picking_confirm_available_picking_rel',
                                             'picking_confirm_id', 'available_picking_id',
                                             string='Available Stock Picking')
    picking_ids = fields.Many2many('stock.picking', 'dpt_picking_confirm_picking_rel', 'picking_confirm_id',
                                   'picking_id',
                                   string='Picking')
    shipping_id = fields.Many2one('dpt.shipping.slip', string='Shipping Slip')

    def action_confirm_picking(self):
        for picking_id in self.picking_ids:
            picking_id.action_confirm()
            picking_id.button_validate()
