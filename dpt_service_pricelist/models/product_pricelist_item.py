import json

from odoo import fields, models, api


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer_rank', '>', 0)])
    service_id = fields.Many2one('dpt.service.management', 'Service')
    uom_id = fields.Many2one('uom.uom', string='Unit')
    version = fields.Integer('Version', default=1)
    percent_based_on = fields.Selection([
        ('product_total_amount', 'Product Total Amount'),
        ('declaration_total_amount', 'Declaration Total Amount')
    ], 'Based On')
    min_amount = fields.Float(string="Min Amount", digits='Product Price')
    # re define
    compute_price = fields.Selection(
        selection=[
            ('fixed', "Fixed Price"),
            ('percentage', "Discount"),
            # ('formula', "Formula"),
            ('table', "Table"),
        ],
        index=True, default='fixed', required=True)

    @api.onchange('service_id')
    def onchange_service(self):
        return {
            'domain': {'uom_id': [('id', 'in', self.service_id.uom_ids.ids)]}
        }
