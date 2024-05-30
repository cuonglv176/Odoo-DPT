from odoo import models, fields, api, _
from datetime import datetime


class DPTSaleChangePrice(models.Model):
    _name = 'dpt.sale.change.price'

    def _default_data_service(self):
        order_id = self.env['sale.order'].browse(
            self.env.context.get('active_id') or self.env.context.get('default_order_id'))
        services = []
        if order_id:
            for r in order_id.sale_service_ids:
                services.append((0, 0, {
                    'service_id': r.service_id.id,
                    'qty': r.qty,
                    'price': r.price,
                    'currency_id': order_id.company_id.currency_id.id,
                    'amount_total': r.amount_total,
                }))
        return services or False

    def _default_data_product(self):
        order_id = self.env['sale.order'].browse(
            self.env.context.get('active_id') or self.env.context.get('default_order_id'))
        products = []
        if order_id:
            for r in order_id.order_line:
                products.append((0, 0, {
                    'product_id': r.product_template_id.id,
                    'qty': r.product_uom_qty,
                    'price': r.price_unit,
                    'currency_id': order_id.company_id.currency_id.id,
                    'amount_total': r.price_subtotal,
                }))
        return products or False

    order_id = fields.Many2one('sale.order')
    service_ids = fields.One2many('dpt.sale.change.price.service.line', 'parent_id', default=_default_data_service)
    product_ids = fields.One2many('dpt.sale.change.price.product.line', 'parent_id', default=_default_data_product)

    def send_request(self):
        return
