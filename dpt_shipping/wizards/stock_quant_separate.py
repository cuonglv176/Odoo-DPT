# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockQuantSeparate(models.TransientModel):
    _name = 'stock.quant.separate'

    quant_ids = fields.Many2many('stock.quant', string="Stock Quant")
    lot_ids = fields.Many2many('stock.lot', string="Stock Quant")
    product_ids = fields.Many2many('product.product', string="Product")
    detail_ids = fields.One2many('stock.quant.separate.line', 'quant_separate_id', 'Detail')

    def action_update_quant(self):
        new_quantity = {}
        for detail_id in self.detail_ids:
            quant_id = detail_id.quant_id
            if quant_id in new_quantity:
                list_quantity = new_quantity[quant_id]
                list_quantity.append(detail_id.new_quantity)
                new_quantity[quant_id] = list_quantity
            else:
                new_quantity[quant_id] = [detail_id.new_quantity]
        new_quant_ids = self.env['stock.quant']
        for quant_id, list_quantity in new_quantity.items():
            for index, quantity in enumerate(list_quantity):
                if index == 0:
                    quant_id.inventory_quantity = quantity
                    new_quant_ids |= quant_id
                else:
                    new_quant_id = quant_id.copy({
                        'inventory_quantity': quantity
                    })
                    new_quant_ids |= new_quant_id

        # new_quant_ids.action_apply_inventory()
