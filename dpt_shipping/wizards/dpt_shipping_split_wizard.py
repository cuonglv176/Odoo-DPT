# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class DPTShippingSplitWizard(models.TransientModel):
    _name = 'dpt.shipping.split.wizard'

    available_sale_ids = fields.Many2many('sale.order', 'dpt_shipping_split_available_sale_rel', 'shipping_slip_id',
                                          'available_sale_id', string='Available Sale Order')
    sale_ids = fields.Many2many('sale.order', 'dpt_shipping_split_sale_rel', 'shipping_slip_id', 'sale_id',
                                string='Sale Order')

    available_picking_ids = fields.Many2many('stock.picking', 'dpt_shipping_split_available_picking_rel',
                                             'shipping_split_id', 'available_picking_id',
                                             string='Available Stock Picking')
    picking_ids = fields.Many2many('stock.picking', 'dpt_shipping_split_picking_rel', 'shipping_split_id', 'picking_id',
                                   string='Picking')
    shipping_id = fields.Many2one('dpt.shipping.slip', string='Shipping Slip')
    location_dest_id = fields.Many2one('stock.location', 'Destination Location')

    def create_shipping_receive(self):
        for picking_id in self.picking_ids:
            picking_id.create_in_transfer_picking(self.location_dest_id)
        in_picking_ids = self.picking_ids.mapped('x_in_transfer_picking_id')
        export_import_ids = self.env['dpt.export.import.line'].sudo().search(
            [('sale_id', 'in', in_picking_ids.mapped('sale_purchase_id').ids)]).mapped('export_import_id') | self.env[
                                'dpt.export.import'].sudo().search(
            [('sale_id', 'in', in_picking_ids.mapped('sale_purchase_id').ids)])
        shipping_slip_receive_id = self.env['dpt.shipping.slip'].create({
            'send_shipping_id': self.shipping_id.id,
            'sale_ids': in_picking_ids.mapped('sale_purchase_id').ids,
            'in_picking_ids': in_picking_ids.ids,
            'export_import_ids': export_import_ids.ids,
        })
        return {
            'name': "Shipping Slip Receive",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.shipping.slip',
            'target': 'self',
            'view_mode': 'form',
            'res_id': shipping_slip_receive_id.id,
            'views': [(False, 'form')],
        }
