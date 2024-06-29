# -*- coding: utf-8 -*-

from odoo import models, fields, api


class UomUom(models.Model):
    _inherit = 'uom.uom'

    product_id = fields.Many2one('product.product', 'Product')
