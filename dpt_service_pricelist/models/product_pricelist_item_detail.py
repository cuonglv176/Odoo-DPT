from odoo import fields, models, api


class ProductPricelistItemDetail(models.Model):
    _name = 'product.pricelist.item.detail'

    item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    amount = fields.Float(string="Amount", digits='Product Price')
    compute_price = fields.Selection(
        selection=[
            ('fixed', "Fixed Price"),
            ('percentage', "Percentage"),
            # ('formula', "Formula"),
            ('table', "Table"),
        ],
        index=True, default='fixed', required=True)
    uom_id = fields.Many2one('uom.uom', string="UoM")
    description = fields.Char('Description')
