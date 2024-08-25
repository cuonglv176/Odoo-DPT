# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_product_deposit = fields.Boolean('Là sản phẩm cọc', default=False)
    is_product_buy = fields.Boolean('Là sản phẩm mua hộ', default=False)

    @api.constrains('is_product_deposit')
    def constraint_is_product_deposit(self):
        for product in self:
            product_deposit_id = self.env['product.template'].search(
                [('is_product_deposit', '=', True), ('id', '!=', product.id)])
            if len(product_deposit_id) > 1:
                raise ValidationError(_("Chỉ có một sản phẩm cọc"))

    @api.constrains('is_product_buy')
    def constraint_is_product_buy(self):
        for product in self:
            product_buy_id = self.env['product.template'].search(
                [('is_product_buy', '=', True), ('id', '!=', product.id)])
            if len(product_buy_id) > 1:
                raise ValidationError(_("Chỉ có một sản phẩm mua hộ"))
