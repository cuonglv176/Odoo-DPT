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
        pass

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
        pass

    @api.depends('sale_service_ids.amount_total')
    def _compute_service_amount(self):
        untax_amount = 0
        tax_amount = 0
        for r in self.sale_service_ids:
            untax_amount += r.amount_total
            tax_amount += 0
        self.service_total_untax_amount = untax_amount
        self.service_tax_amount = tax_amount
        self.service_total_amount = untax_amount + tax_amount


class DPTSaleChangePrice(models.Model):
    _name = 'dpt.sale.change.price'


class DPTSaleChangePriceLine(models.Model):
    _name = 'dpt.sale.change.price.line'

