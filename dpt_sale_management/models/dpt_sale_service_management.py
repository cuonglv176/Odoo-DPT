from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DPTSaleServiceManagement(models.Model):
    _name = 'dpt.sale.service.management'
    _description = 'DPT Sale Service Management'

    sale_id = fields.Many2one('sale.order', ondelete='cascade')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY', default=1)
    uom_ids = fields.Many2many(related='service_id.uom_ids')
    uom_id = fields.Many2one('uom.uom', string='Unit', domain="[('id', 'in', uom_ids)]")
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    department_id = fields.Many2one(related='service_id.department_id')
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")
    sequence = fields.Integer()
    pricelist_item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')
    price_in_pricelist = fields.Monetary(currency_field='currency_id', string='Price in Pricelist')
    compute_uom_id = fields.Many2one('uom.uom', 'Compute Unit')
    compute_value = fields.Float('Compute Value')

    def write(self, vals):
        old_price = self.price
        res = super(DPTSaleServiceManagement, self).write(vals)
        new_price = self.price
        if self.env.context.get('final_approved', False):
            return res
        if old_price > new_price:
            raise UserError(_("Cannot lower price, only increase price."))
        return res

    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.qty * item.price * item.compute_value if item.pricelist_item_id.is_price else item.qty * item.price

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = self.price * self.qty * self.compute_value if self.pricelist_item_id.is_price else self.qty * self.price

    @api.onchange('service_id')
    def onchange_service(self):
        if self.service_id:
            self.uom_id = self.service_id.uom_id
