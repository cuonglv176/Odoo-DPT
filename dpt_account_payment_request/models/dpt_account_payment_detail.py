from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DPTAccountPaymentDetail(models.Model):
    _name = 'dpt.account.payment.detail'
    _description = 'DPT Account Payment Detail'

    sequence = fields.Integer(string='Sequence')
    product_id = fields.Many2one('product.product', string='Product')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    payment_id = fields.Many2one('account.payment', string='Payment')
    payment_product_id = fields.Many2one('account.payment', string='Payment Product')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY', default=1)
    uom_ids = fields.Many2many(related='service_id.uom_ids')
    uom_id = fields.Many2one('uom.uom', string='Chi tiết dịch vụ', domain="[('id', 'in', uom_ids)]")
    compute_uom_id = fields.Many2one('uom.uom', 'Đơn vị tính')
    department_id = fields.Many2one(related='service_id.department_id')

    price = fields.Monetary(currency_field='currency_id', string='Price')
    price_cny = fields.Monetary(currency_field='currency_cny_id', string='Price CNY')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")

    def write(self, vals):
        res = super(DPTAccountPaymentDetail, self).write(vals)
        self.onchange_update_amount_payment()
        return res

    @api.model
    def create(self, vals):
        res = super(DPTAccountPaymentDetail, self).create(vals)
        self.onchange_update_amount_payment()
        return res

    def onchange_update_amount_payment(self):
        amount = 0
        if self.payment_id:
            for detail_id in self.payment_id.detail_ids:
                amount += detail_id.amount_total
            self.payment_id.amount = amount

    @api.onchange('price_cny')
    def onchange_price_cny(self):
        self.price = self.price_cny * self.currency_cny_id.rate

    @api.depends('price', 'qty')
    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.qty * item.price
