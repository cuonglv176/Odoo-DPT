# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    package_line_id = fields.Many2one('purchase.order.line.package', 'Package Line')
    is_package = fields.Boolean('Is Package', compute="_compute_is_package", search="_search_is_package")

    def _compute_is_package(self):
        for item in self:
            package_id = self.env['uom.uom'].search([('product_id', '=', item.product_id.id)], limit=1)
            item.is_package = True if package_id else False

    def _search_is_package(self, operator, operand):
        """
        Allow the "mapped" and "not mapped" filters in the account list views.
        """
        product_of_package_ids = self.env['uom.uom'].search([('is_package_unit', '=', True)]).mapped('product_id')
        operator = 'in' if (operator == '=' and operand) or (operator == '!=' and not operand) else 'not in'
        return [('product_id', operator, product_of_package_ids.ids)]