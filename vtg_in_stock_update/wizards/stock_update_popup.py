# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import xlrd
import base64

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockUpdatePopup(models.TransientModel):
    _name = 'stock.update.popup'
    _description = 'Popup for update in-stock'

    filedata = fields.Binary(string='Import file')
    filename = fields.Char()
    location_id = fields.Many2one('stock.location', 'Location')

    def action_update_in_stock(self):
        if not self.filedata:
            raise ValidationError("Vui lòng import file dữ liệu!")
        try:
            book = xlrd.open_workbook(file_contents=base64.decodebytes(self.filedata))
            sheet = book.sheet_by_index(0)
        except:
            raise ValidationError("File import không đúng định dạng xlsx, xls")
        row = 1
        while row < sheet.nrows:
            id = sheet.cell(row, 0).value
            quantity = sheet.cell(row, 3).value
            standard_price = sheet.cell(row, 4).value
            lst_price = sheet.cell(row, 5).value
            product_id = self.env['product.product'].search([('id', '=', id)])
            if not product_id or (product_id and product_id.type in ('consu', 'service')):
                row += 1
                continue
            # xóa các stock move đang giữ hàng
            outgoing_stock_move_ids = self.env['stock.move.line'].sudo().search(
                [('location_id', '=', self.location_id.id), ('product_id', '=', product_id.id),
                 ('state', '!=', 'done')])
            for item in outgoing_stock_move_ids:
                try:
                    item.unlink()
                except:
                    continue
            # tạo quant
            quant_id = self.env['stock.quant'].search(
                [('location_id', '=', self.location_id.id), ('product_id', '=', product_id.id)])
            if quant_id:
                quant_id.update({
                    'inventory_quantity': quantity,
                    'user_id': self.env.user.id
                })
            else:
                quant_id = self.env['stock.quant'].sudo().create({
                    'product_id': product_id.id,
                    'location_id': self.location_id.id,
                    'inventory_quantity': quantity,
                    'inventory_date': fields.Date.context_today(self.env.user),
                    'user_id': self.env.user.id
                })
            quant_id.action_apply_inventory()

            product_id.update({
                'lst_price': lst_price,
                'standard_price': standard_price
            })
            row += 1

    def action_update_product_supplier(self):
        if not self.filedata:
            raise ValidationError("Vui lòng import file dữ liệu!")
        try:
            book = xlrd.open_workbook(file_contents=base64.decodebytes(self.filedata))
            sheet = book.sheet_by_index(0)
        except:
            raise ValidationError("File import không đúng định dạng xlsx, xls")
        row = 1
        data = []
        while row < sheet.nrows:
            product_id = int(sheet.cell(row, 0).value)
            supplier_ref = sheet.cell(row, 4).value
            if not supplier_ref:
                row += 1
                continue
            supplier_id = self.env['res.partner'].sudo().search([('x_partner_code', '=', supplier_ref)], limit=1)
            if not supplier_id:
                row += 1
                continue
            supplierinfo_id = self.env['product.supplierinfo'].sudo().search(
                [('name', '=', supplier_id.id), ('product_id', '=', product_id)])
            if supplierinfo_id:
                row += 1
                continue
            data.append({
                'product_id': product_id,
                'name': supplier_id.id
            })
            row += 1
        if data:
            self.env['product.supplierinfo'].sudo().create(data)
