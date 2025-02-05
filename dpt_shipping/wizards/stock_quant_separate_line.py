# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockQuantSeparateLine(models.TransientModel):
    _name = 'stock.quant.separate.line'
    # _inherit = 'stock.quant'

    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    quant_id = fields.Many2one('stock.quant', 'Stock Quant')
    lot_id = fields.Many2one('stock.lot', 'Stock Lot')
    location_id = fields.Many2one('stock.location', 'Stock Location')
    quant_separate_id = fields.Many2one('stock.quant.separate', string="Quant Separate")
    new_quantity = fields.Integer('New Quantity')

    @api.onchange('lot_id', 'product_id')
    def onchange_get_detail_information(self):
        if self.lot_id and self.product_id:
            quant_id = self.quant_separate_id.quant_ids.filtered(
                lambda sq: sq.product_id.id == self.product_id.id and sq.lot_id.id == self.lot_id.id)._origin
            other_detail_ids = self.quant_separate_id.detail_ids.filtered(
                lambda dt: dt.quant_id.id == quant_id.id and dt.id != self.id)
            self.quant_id = quant_id.id
            self.location_id = quant_id.location_id.id
            self.quantity = quant_id.quantity
            self.new_quantity = quant_id.quantity - sum(other_detail_ids.mapped('new_quantity'))
