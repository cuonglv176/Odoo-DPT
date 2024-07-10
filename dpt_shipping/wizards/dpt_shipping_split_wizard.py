# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class DPTShippingSplitWizard(models.TransientModel):
    _name = 'dpt.shipping.split.wizard'

    available_sale_ids = fields.Many2many('sale.order', 'dpt_shipping_split_available_sale_rel', 'shipping_slip_id',
                                          'available_sale_id', string='Available Sale Order')
    sale_ids = fields.Many2many('sale.order', 'dpt_shipping_split_sale_rel', 'shipping_slip_id', 'sale_id',
                                string='Sale Order')
    shipping_id = fields.Many2one('dpt.shipping.slip', string='Shipping Slip')

    def create_shipping_receive(self):
        picking_ids = self.env['stock.picking'].sudo().search(
            [('x_transfer_code', '=', 'outgoing_transfer'),
             ('picking_in_id', 'in', self.shipping_id.picking_ids.ids)]).mapped('x_in_transfer_picking_id')
        shipping_id = self.env['dpt.shipping.slip'].create({
            'send_shipping_id': self.shipping_id.id,
            'sale_ids': self.sale_ids.ids,
            'picking_ids': picking_ids.ids,
        })
