from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DPTSaleServiceManagement(models.Model):
    _name = 'dpt.sale.service.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'DPT Sale Service Management'

    sale_id = fields.Many2one('sale.order', ondelete='cascade')
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
    compute_value = fields.Float('Compute Value', default=1)
    note = fields.Text(string='Note')

    # def unlink(self):
    #     res = super(DPTSaleServiceManagement, self).unlink()
    #     for record in self:
    #         if record.sale_id:
    #             message = f"Dịch vụ bị xoá: {record.service_id}"
    #             record.sale_id.message_post(body=message, message_type='comment')
    #     return res
    #
    # def write(self, vals):
    #     old_values = {rec.id: rec.read(vals.keys())[0] for rec in self}
    #     res = super(DPTSaleServiceManagement, self).write(vals)
    #     self.action_confirm_quote()
    #     self.action_check_status_sale_order()
    #     for rec in self:
    #         if rec.sale_id:
    #             changes = []
    #             for field, new_value in vals.items():
    #                 old_value = old_values[rec.id].get(field)
    #                 if old_value != new_value:
    #                     changes.append(f"{field}: {old_value} -> {new_value}")
    #             if changes:
    #                 message = f"Thông tin dịch vụ thay đổi: {rec.service_id.name}: " + ", ".join(changes)
    #                 rec.sale_id.message_post(body=message, message_type='comment')
    #     return res

    def action_check_status_sale_order(self):
        if self.sale_id.locked:
            raise UserError(_(f'Đơn hàng {self.sale_id.name} đang khoá, vui lòng mở khoá trước khi update dịch vụ!!!.'))

    def action_confirm_quote(self):

        if self.sale_id.state in ('sent', 'sale'):
            return
        a = 1
        # a = 0
        # for line in self.sale_id.sale_service_ids:
        #     if line.price < 1 or line.price_status == 'wait_approve':
        #         a = 1
        if all(line.price_status in ('quoted', 'approved', 'approved_approval') for line in
               self.sale_id.sale_service_ids):
            a = 0
        if a == 0:
            self.sale_id.state = 'sent'

    @api.onchange('price_cny')
    def onchange_price_cny(self):
        self.price = self.price_cny * self.currency_cny_id.rate

    # def write(self, vals):
    #     old_price = self.price
    #     res = super(DPTSaleServiceManagement, self).write(vals)
    #     new_price = self.price
    #     if self.env.context.get('final_approved', False):
    #         return res
    #     if old_price > new_price:
    #         raise UserError(_("Cannot lower price, only increase price."))
    #     return res

    @api.depends('qty', 'price', 'compute_value')
    def _compute_amount_total(self):
        for item in self:
            if item.pricelist_item_id.is_price and item.pricelist_item_id.compute_price == 'table':
                item.amount_total = item.qty * item.price * item.compute_value
            elif not item.pricelist_item_id.is_price and item.pricelist_item_id.compute_price == 'table':
                item.amount_total = item.price
            else:
                item.amount_total = item.compute_value * item.price

    @api.onchange('price', 'qty', 'compute_value')
    def onchange_amount_total(self):
        if self.price and self.qty:
            if self.pricelist_item_id.is_price and self.pricelist_item_id.compute_price == 'table':
                self.amount_total = self.price * self.qty * self.compute_value
            elif not self.pricelist_item_id.is_price and self.pricelist_item_id.compute_price == 'table':
                self.amount_total = self.price
            else:
                self.amount_total = self.compute_value * self.price

    @api.onchange('service_id')
    def onchange_service(self):
        if self.service_id:
            self.uom_id = self.service_id.uom_id

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        self.with_context(from_pricelist=True).write({
            'amount_total': 0,
            'price': 0,
            'qty': 1,
            'pricelist_item_id': None,
            'price_in_pricelist': 0,
            'compute_value': 1,
            'compute_uom_id': None,
        })
