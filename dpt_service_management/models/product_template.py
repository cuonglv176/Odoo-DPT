# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_product_service = fields.Boolean('Is Product Service', default=False)

    # @api.constrains('is_product_service')
    # def constraint_product_service(self):
    #     for product in self:
    #         product_service_id = self.env['product.template'].search(
    #             [('is_product_service', '=', True), ('id', '!=', product.id)])
    #         if len(product_service_id) > 1:
    #             raise ValidationError(_("Please configurate ony 1 product as Service product"))
