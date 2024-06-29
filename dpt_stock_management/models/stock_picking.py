# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_code = fields.Char('Transfer Code')
    transfer_code_chinese = fields.Char('Transfer Code in Chinese')
    package_ids = fields.One2many('purchase.order.line.package', 'picking_id', 'Packages')
    move_ids_product = fields.One2many('stock.move', 'picking_id', string="Stock move",
                                       domain=[('is_package', '=', False)], copy=False)

    def create(self, vals):
        res = super().create(vals)
        # getname if it is incoming picking in Chinese stock
        if res.picking_type_code == 'incoming' and res.location_dest_id.warehouse_id.is_main_incoming_warehouse:
            prefix = f'KT{datetime.now().strftime("%y%m%d")}'
            nearest_picking_id = self.env['stock.picking'].sudo().search(
                [('name', 'ilike', prefix + "%"), ('id', '!=', res.id),
                 ('picking_type_id.code', '=', res.picking_type_code)], order='id desc', limit=1)
            if nearest_picking_id:
                try:
                    number = int(nearest_picking_id.name[7:])
                except:
                    number = 0
                res.name = prefix + str(number).zfill(3)
            else:
                res.name = prefix + '001'
        else:
            pass
        return res
