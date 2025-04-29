# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockQuantExport(models.TransientModel):
    _name = 'stock.quant.export'

    quant_ids = fields.Many2many('stock.quant', string="Stock Quant")
    ticket_ids = fields.Many2many('helpdesk.ticket', string='Ticket')

    def action_export(self):
        self.quant_ids.write({
            'ticket_ids': self.ticket_ids.ids
        })
        # group quant based on partner
        quant_combine = {}
        for quant_id in self.quant_ids:
            lot_id = quant_id.lot_id
            main_incoming_picking_id = self.env['stock.picking'].sudo().search(
                [('is_main_incoming', '=', True), ('picking_lot_name', '=', lot_id.name)], limit=1)
            if not main_incoming_picking_id:
                raise ValidationError("Please check main incoming of lot: %s" % lot_id.name)
            partner_id = main_incoming_picking_id.sale_purchase_id.partner_id
            if partner_id in quant_combine:
                quant_combine[partner_id] = quant_combine.get(partner_id) | quant_id
            else:
                quant_combine[partner_id] = quant_id
        export_picking_ids = self.env['stock.picking']
        export_picking_vals = []
        for partner_id, quant_ids in quant_combine.items():
            for quant_id in quant_ids:
                uom_id = self.env['uom.uom'].sudo().search([('product_id', '=', quant_id.product_id.id)], limit=1)
                picking_type_id = self.env['stock.picking.type'].sudo().search(
                    [('code', '=', 'outgoing'), ('warehouse_id', '=', quant_id.location_id.warehouse_id.id)], limit=1)
                export_picking_vals.append({
                    'partner_id': partner_id.id,
                    'location_id': quant_ids[0].location_id.id,
                    'location_dest_id': partner_id.property_stock_customer.id,
                    'picking_type_id': picking_type_id.id,
                    'picking_lot_name': quant_id.lot_id.name,
                    'package_ids': [(0, 0, {
                        'uom_id': uom_id.id,
                        'quantity': quant_id.quantity,
                        'transfer_quantity': quant_id.quantity,
                        # 'length': package_id.length,
                        # 'width': package_id.width,
                        # 'height': package_id.height,
                        # 'size': package_id.size,
                        # 'total_weight': math.ceil(round(package_id.weight * package_id.transfer_quantity, 2)) * (package_id.transfer_quantity - package_id.created_picking_qty) / package_id.transfer_quantity,
                        # 'weight': package_id.weight,
                        # 'volume': package_id.volume,
                        # 'total_volume': (math.ceil(round(package_id.volume * package_id.transfer_quantity * 100, 4)) / 100) * (package_id.transfer_quantity - package_id.created_picking_qty) / package_id.transfer_quantity,
                    })]
                })
                export_picking_id = self.env['stock.picking'].create(export_picking_vals)
                export_picking_id.move_line_ids.write({
                    'lot_id': quant_id.lot_id.id,
                })
                export_picking_ids |= export_picking_id
        if export_picking_ids:
            shipping_id = self.env['dpt.shipping.slip'].create({
                'out_picking_ids': export_picking_ids.ids,
                'ticket_ids': self.ticket_ids.ids,
                'last_shipping_slip': True,
                'delivery_slip_type': 'last_delivery_vn',
            })

        return {
            'res_model': 'dpt.shipping.slip',
            'name': "Phiếu vận chuyển",
            'views': [[False, 'form']],
            'view_mode': 'form',
            'target': 'self',
            'type': 'ir.actions.act_window',
            'res_id': shipping_id.id
        }
