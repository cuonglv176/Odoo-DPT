from odoo import models, fields, api, _
from datetime import datetime


class DPTSaleServiceManagement(models.Model):
    _name = 'dpt.sale.service.management'
    _description = 'DPT Sale Service Management'

    sale_id = fields.Many2one('sale.order', ondelete='cascade')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one(related='service_id.uom_id')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    department_id = fields.Many2one(related='service_id.department_id')
    amount_total = fields.Float(string="Amount Total")
    # status = fields.Selection(related='service_id.state')
    status = fields.Char(string='Status')
    sequence = fields.Integer()

    def action_calculation(self):
        return {
            'name': "Calculation Service",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.sale.calculation',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_service_id': self.service_id.id,
            },
        }

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = self.price * self.qty


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_service_ids = fields.One2many('dpt.sale.service.management', 'sale_id', string='Service')
    service_total_untax_amount = fields.Float(compute='_compute_service_amount')
    service_tax_amount = fields.Float(compute='_compute_service_amount')
    service_total_amount = fields.Float(compute='_compute_service_amount')

    def send_quotation_department(self):
        pass

    def action_change_price(self):
        return {
            'name': "Change Price",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.sale.change.price',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_order_id': self.id,
            },
        }

    @api.depends('sale_service_ids.amount_total')
    def _compute_service_amount(self):
        untax_amount = 0
        tax_amount = 0
        for r in self.sale_service_ids:
            untax_amount += r.amount_total
            tax_amount += r.amount_total*8/100
        self.service_total_untax_amount = untax_amount
        self.service_tax_amount = tax_amount
        self.service_total_amount = untax_amount + tax_amount


class DPTSaleChangePrice(models.Model):
    _name = 'dpt.sale.change.price'

    def _default_data_service(self):
        order_id = self.env['sale.order'].browse(self.env.context.get('active_id') or self.env.context.get('default_order_id'))
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
        order_id = self.env['sale.order'].browse(self.env.context.get('active_id') or self.env.context.get('default_order_id'))
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
    service_ids = fields.One2many('dpt.sale.change.price.servie.line', 'parent_id', default=_default_data_service)
    product_ids = fields.One2many('dpt.sale.change.price.product.line', 'parent_id', default=_default_data_product)

    def send_request(self):
        return


class DPTSaleChangePriceServiceLine(models.Model):
    _name = 'dpt.sale.change.price.servie.line'

    parent_id = fields.Many2one('dpt.sale.change.price')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    qty = fields.Float(string='QTY')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    change_price = fields.Monetary(currency_field='currency_id', string='Change Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")


class DPTSaleChangePriceProductLine(models.Model):
    _name = 'dpt.sale.change.price.product.line'

    parent_id = fields.Many2one('dpt.sale.change.price')
    product_id = fields.Many2one('product.template', string='Product')
    qty = fields.Float(string='QTY')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    change_price = fields.Monetary(currency_field='currency_id', string='Change Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")


class DPTSaleCalculattion(models.Model):
    _name = 'dpt.sale.calculation'

    def _default_service_id(self):
        return self.env.context.get('active_id') or self.env.context.get('default_service_id')

    service_id = fields.Many2one('dpt.service.management', default=_default_service_id)
    service_ids = fields.One2many('dpt.sale.calculation.line', 'parent_id')


class DPTSaleCalculattionLine(models.Model):
    _name = 'dpt.sale.calculation.line'

    parent_id = fields.Many2one('dpt.sale.calculation')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one('uom.uom')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")


