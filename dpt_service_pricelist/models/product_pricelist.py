from odoo import fields, models, api


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer_rank', '>', 0)])