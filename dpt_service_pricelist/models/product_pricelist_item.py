import json

from odoo import fields, models, api


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer_rank', '>', 0)])
    service_id = fields.Many2one('dpt.service.management', 'Service')
    service_uom_ids = fields.Many2many(related='service_id.uom_ids')
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
            ('percentage', "Percentage"),
            ('table', "Table"),
        ],
        index=True, default='fixed', required=True)
    pricelist_table_detail_ids = fields.One2many('product.pricelist.item.detail', 'item_id', string='Pricelist Table')
    is_price = fields.Boolean('Is Price')

    @api.onchange('service_id')
    def onchange_service(self):
        return {
            'domain': {'uom_id': [('id', 'in', self.service_id.uom_ids.ids)]}
        }

    @api.model
    def create(self, vals):
        if not vals.get('pricelist_id', False):
            partner_id = vals.get('partner_id', False)
            currency_id = vals.get('currency_id', False)
            if partner_id:
                pricelist_id = self.env['product.pricelist'].search(
                    [('partner_id', '=', partner_id), ('currency_id', '=', currency_id),
                     ('company_id', '=', self.env.company.id)], limit=1)
                if not pricelist_id:
                    partner_obj_id = self.env['res.partner'].sudo().browse(partner_id)
                    pricelist_id = self.env['product.pricelist'].create({
                        'name': 'Bảng giá khách hàng %s' % partner_obj_id.name,
                        'partner_id': partner_id,
                        'currency_id': currency_id,
                        'company_id': self.env.company.id
                    })
                    vals['pricelist_id'] = pricelist_id.id
            else:
                pricelist_id = self.env['product.pricelist'].search(
                    [('partner_id', '=', False), ('currency_id', '=', currency_id),
                     ('company_id', '=', self.env.company.id)], limit=1)
                if not pricelist_id:
                    pricelist_id = self.env['product.pricelist'].create({
                        'name': 'Bảng giá chung',
                        'currency_id': currency_id,
                        'company_id': self.env.company.id
                    })
                vals['pricelist_id'] = pricelist_id.id
        return super().create(vals)
