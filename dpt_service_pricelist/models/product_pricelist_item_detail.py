from odoo import fields, models, api


class ProductPricelistItemDetail(models.Model):
    _name = 'product.pricelist.item.detail'

    item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    version = fields.Integer('Version', default=1)
    percent_based_on = fields.Selection([
        ('product_total_amount', 'Product Total Amount'),
        ('declaration_total_amount', 'Declaration Total Amount')
    ], 'Based On')
    min_amount = fields.Float(string="Min Amount", digits='Product Price')
