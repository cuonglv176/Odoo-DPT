# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockQuantExport(models.TransientModel):
    _name = 'stock.quant.export'

    quant_ids = fields.Many2many('stock.quant', string="Stock Quant")
    ticket_id = fields.Many2one('helpdesk.ticket', 'Ticket')

    def action_export(self):
        self.quant_ids.write({
            'ticket_id': self.ticket_id.id
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
        for partner_id, quant_ids in quant_combine.items():
            export_picking_vals = {
                'partner_id': partner_id.id,
                'location_id': quant_ids[0].location_id.id,
                'location_dest_id': partner_id.property_stock_customer.id,
            }
