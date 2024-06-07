import json

from odoo import fields, models, api


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals_list):
        res = super(MailMessage, self).create(vals_list)
        if res.model == 'product.pricelist.item':
            obj_data = self.env[res.model].browse(res.res_id)
            res.res_id = obj_data.service_id.id
            res.model = 'dpt.service.management'
        return res


class ProductPricelistItem(models.Model):
    _name = 'product.pricelist.item'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'product.pricelist.item']

    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer_rank', '>', 0)], tracking=True)
    service_id = fields.Many2one('dpt.service.management', 'Service', tracking=True)
    service_uom_ids = fields.Many2many(related='service_id.uom_ids', tracking=True)
    uom_id = fields.Many2one('uom.uom', string='Unit', tracking=True)
    version = fields.Integer('Version', default=1, tracking=True)
    percent_based_on = fields.Selection([
        ('product_total_amount', 'Product Total Amount'),
        ('declaration_total_amount', 'Declaration Total Amount')
    ], 'Based On', tracking=True)
    min_amount = fields.Float(string="Min Amount", digits='Product Price', tracking=True)
    # re define
    compute_price = fields.Selection(
        selection=[
            ('fixed', "Fixed Price"),
            ('percentage', "Percentage"),
            ('table', "Table"),
        ],
        index=True, default='fixed', required=True, tracking=True)
    pricelist_table_detail_ids = fields.One2many('product.pricelist.item.detail', 'item_id', string='Pricelist Table', tracking=True)
    is_price = fields.Boolean('Is Price', tracking=True)

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
