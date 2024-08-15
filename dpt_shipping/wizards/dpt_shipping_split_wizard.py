# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class DPTShippingSplitWizard(models.TransientModel):
    _name = 'dpt.shipping.split.wizard'

    available_sale_ids = fields.Many2many('sale.order', 'dpt_shipping_split_available_sale_rel', 'shipping_slip_id',
                                          'available_sale_id', string='Available Sale Order')
    sale_ids = fields.Many2many('sale.order', 'dpt_shipping_split_sale_rel', 'shipping_slip_id', 'sale_id',
                                string='Sale Order')

    available_picking_ids = fields.Many2many('sale.order', 'dpt_shipping_split_available_picking_rel',
                                             'shipping_split_id', 'available_picking_id',
                                             string='Available Stock Picking')
    picking_ids = fields.Many2many('stock.picking', 'dpt_shipping_split_picking_rel', 'shipping_split_id', 'picking_id',
                                   string='Picking')
    shipping_id = fields.Many2one('dpt.shipping.slip', string='Shipping Slip')

    def create_shipping_receive(self):
        export_import_ids = self.env['dpt.export.import'].sudo().search(
            [('sale_id', 'in', self.picking_ids.mapped('sale_purchase_id').ids)])
        self.env['dpt.shipping.slip'].create({
            'send_shipping_id': self.shipping_id.id,
            'sale_ids': self.picking_ids.mapped('sale_purchase_id').ids,
            'out_picking_ids': self.picking_ids.ids,
            'export_import_ids': export_import_ids.ids,
        })
