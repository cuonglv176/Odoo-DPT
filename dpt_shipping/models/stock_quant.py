# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, SUPERUSER_ID


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    ticket_ids = fields.Many2many('helpdesk.ticket', string='Ticket')

    def action_stock_quant_separate(self):
        context = {
            'default_quant_ids': self.ids,
            'default_lot_ids': self.mapped('lot_id').ids,
            'default_product_ids': self.mapped('lot_id.product_id').ids,
            'default_detail_ids': [(0, 0, {
                'product_id': item.product_id.id,
                'quant_id': item.id,
                'location_id': item.location_id.id,
                'lot_id': item.lot_id.id,
                'quantity': item.quantity,
                'new_quantity': item.quantity
            }) for item in self]
        }
        return {
            'res_model': 'stock.quant.separate',
            'views': [[False, 'form']],
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': context,
        }

    def action_stock_quant_export(self):
        return {
            'res_model': 'stock.quant.export',
            'views': [[False, 'form']],
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_quant_ids': self.ids
            },
        }
