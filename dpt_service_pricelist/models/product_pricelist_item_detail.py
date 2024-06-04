from odoo import fields, models, api


class ProductPricelistItemDetail(models.Model):
    _name = 'product.pricelist.item.detail'

    item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    amount = fields.Float(string="Amount", digits='Product Price')
    uom_id = fields.Many2one('uom.uom', 'Product Units')
    description = fields.Char('Description')
    min_value = fields.Float('Min Value')
    max_value = fields.Float('Max Value')
