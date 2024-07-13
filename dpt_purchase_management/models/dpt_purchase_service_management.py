from odoo import api, fields, models, _


class DPTPurchaseServiceManagement(models.Model):
    _name = 'dpt.purchase.service.management'

    purchase_id = fields.Many2one('purchase.order', ondelete='cascade')
    sale_id = fields.Many2one('sale.order', ondelete='cascade', related="purchase_id.sale_id")
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY', default=1)
    uom_ids = fields.Many2many(related='service_id.uom_ids')
    uom_id = fields.Many2one('uom.uom', string='Service detail', domain="[('id', 'in', uom_ids)]")
    price = fields.Monetary(currency_field='currency_id', string='Price')
    price_cny = fields.Monetary(currency_field='currency_cny_id', string='Price CNY')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
    department_id = fields.Many2one(related='service_id.department_id')
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")
    sequence = fields.Integer()
    pricelist_item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')
    price_in_pricelist = fields.Monetary(currency_field='currency_id', string='Price in Pricelist')
    compute_uom_id = fields.Many2one('uom.uom', 'Compute Unit')
    compute_value = fields.Float('Compute Value')

    @api.depends('price', 'qty')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.qty * rec.price
