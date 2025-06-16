from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.order.service.combo'

    price_status = fields.Selection([
        ('no_price', 'No Price'),  # Chưa có giá
        ('wait_approve', 'Wait Approve'),  # Chờ duyệt giá
        ('approved', 'Approved'),  # Đã duyệt
        ('not_calculate', 'Not Calculate'),
        ('calculated', 'Calculated'),  # Đã tính giá
        ('wait_quotation', 'Chờ báo giá'),
        ('quoted', 'Quoted'),  # Đã báo giá
        ('refuse_quoted', 'Refuse Quoted'),  # Từ chối báo giá
        ('sent_approval', 'Sent Approval'),
        ('approved_approval', 'Approved Approval'),
        ('refuse_approval', 'Refuse Approval'),  # Từ chối duyệt giá
        ('ticket_status', 'Ticket Status'),  # Thực hiện dịch vụ

    ], string='Status', default='no_price', store=True)
    new_price = fields.Monetary(currency_field='currency_id', string='New Price')
    new_amount_total = fields.Monetary(currency_field='currency_id', string="New Amount Total",
                                       compute="_compute_new_amount_total")
    approval_id = fields.Many2one('approval.request', string='Approval Change Price')
    is_zero_price = fields.Boolean(string='Giá 0 Đồng', default=False)
    is_edit_new_price = fields.Boolean(string='Edit new price', compute="_compute_is_edit_new_price", default=False)

    @api.onchange('is_zero_price')
    def update_is_zero_price(self):
        if self.is_zero_price:
            self.new_price = 0

    def write(self, vals):
        for item in self:
            old_price = item.price
            if self.env.context.get('check_price', False) and not self.env.context.get('from_pricelist', False):
                if 'price' in vals:
                    new_price = vals.get('price')
                    # if old_price > new_price and not (
                    #         self._fields.get('purchase_id', False) and not item.purchase_id.last_rate_currency):
                    # if self.user_has_groups('dpt_security.group_dpt_employee_sale'):
                    #     if old_price > new_price:
                    #         raise ValidationError(_(f"Giá mới {new_price} không được nhỏ hơn giá cũ {old_price}!!"))
        return super(DPTSaleServiceManagement, self).write(vals)

    @api.depends('approval_id')
    def _compute_is_edit_new_price(self):
        for rec in self:
            is_edit_new_price = False
            if rec.approval_id:
                for approver_id in rec.approval_id.approver_ids:
                    if self.env.user.id == approver_id.user_id.id:
                        is_edit_new_price = True
            rec.is_edit_new_price = is_edit_new_price

    def action_accept_approval_price(self):
        self.price_status = 'quoted'
        sale_service_quoted = self.sale_id.sale_service_ids.filtered(
            lambda m: m.price_status in ('quoted', 'approved', 'calculated'))
        if len(sale_service_quoted) == len(self.sale_id.sale_service_ids):
            self.sale_id.state = 'sent'

    def action_refuse_approval_price(self):
        self.price_status = 'refuse_quoted'
    @api.depends('new_price', 'qty')
    def _compute_new_amount_total(self):
        for item in self:
            if item.compute_value > 0:
                item.new_amount_total = item.compute_value * item.new_price
            else:
                item.new_amount_total = item.new_price
