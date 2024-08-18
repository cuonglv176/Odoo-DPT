from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    price_status = fields.Selection([
        ('no_price', 'No Price'),  # Chưa có giá
        ('wait_approve', 'Wait Approve'),  # Chờ duyệt giá
        ('approved', 'Approved'),           # Đã duyệt
        ('not_calculate', 'Not Calculate'),
        ('calculated', 'Calculated'),  # Đã tính giá
        ('sent_quotation', 'Sent Quotation'),
        ('quoted', 'Quoted'),  # Đã báo giá
        ('refuse_quoted', 'Refuse Quoted'),  # Từ chối báo giá
        ('sent_approval', 'Sent Approval'),
        ('approved_approval', 'Approved Approval'),
        ('refuse_approval', 'Refuse Approval'), # Từ chối duyệt giá
        ('ticket_status', 'Ticket Status'), # Thực hiện dịch vụ

    ], string='Status', default='no_price', compute="_compute_price_status", store=True)
    new_price = fields.Monetary(currency_field='currency_id', string='New Price')
    new_amount_total = fields.Monetary(currency_field='currency_id', string="New Amount Total",
                                       compute="_compute_new_amount_total")
    approval_id = fields.Many2one('approval.request', string='Approval Change Price')
    is_edit_new_price = fields.Boolean(string='Edit new price', compute="_compute_is_edit_new_price", default=False)

    def write(self, vals):
        old_price = self.price
        rec = super(DPTSaleServiceManagement, self).write(vals)
        if self.env.context.get('check_price', False) and not self.env.context.get('from_pricelist', False):
            if 'price' in vals:
                new_price = self.price
                if old_price > new_price and not (self._fields.get('purchase_id', False) and not self.purchase_id.last_rate_currency):
                    raise ValidationError(_(f"Giá mới {new_price} không được nhỏ hơn giá cũ {old_price}!!"))
        return rec

    @api.depends('approval_id')
    def _compute_is_edit_new_price(self):
        for rec in self:
            is_edit_new_price = False
            if rec.approval_id:
                for approver_id in rec.approval_id.approver_ids:
                    if self.env.user.id == approver_id.user_id.id:
                        is_edit_new_price = True
            rec.is_edit_new_price = is_edit_new_price

    # @api.depends('approval_id')
    # def _compute_price_status(self):
    #     for rec in self:
    #         if rec.approval_id:
    #             not_approved = rec.approval_id.filtered(lambda approval: approval.request_status != 'approved')
    #             if not_approved:
    #                 price_status = 'wait_approve'
    #             else:
    #                 price_status = 'approved'
    #         else:
    #             price_status = 'no_price'
    #         rec.price_status = price_status

    def action_accept_approval_price(self):
        self.price_status = 'quoted'

    def action_refuse_approval_price(self):
        self.price_status = 'refuse_quoted'

    @api.depends('approval_id', 'approval_id.request_status', 'price')
    def _compute_price_status(self):
        for rec in self:
            rec.price_status = 'not_calculate'
            if rec.sale_id.state == 'draft':
                not_approved = rec.approval_id.filtered(
                    lambda approval: approval.request_status in ('pending', 'new'))
                if not_approved:
                    rec.price_status = 'wait_approve'
                    continue
                if not rec.price:
                    rec.price_status = 'no_price'
                else:
                    rec.price_status = 'calculated'
            elif rec.sale_id.state == 'wait_price':
                not_approved = rec.approval_id.filtered(lambda approval: approval.request_status in ('pending', 'new'))
                if not_approved:
                    rec.price_status = 'wait_approve'
                    continue
                if rec.price_status != 'calculated':
                    rec.price_status = 'not_calculate'
                    continue
            elif rec.sale_id.state == 'sent':
                rec.price_status = 'quoted'
            elif rec.sale_id.state == 'sale':
                rec.price_status = 'ticket_status'
            else:
                rec.price_status = 'no_price'

            # if rec.approval_id:
            #     not_approved = rec.approval_id.filtered(lambda approval: approval.request_status in ('pending', 'new'))
            #     if not_approved:
            #         price_status = 'wait_approve'
            #     else:
            #         latest_approved = max(rec.approval_id, key=lambda line: line.date)
            #
            #         if latest_approved.request_status in ('refused', 'cancel'):
            #             price_status = 'no_price'
            #             approved_state = True
            #         else:
            #             price_status = 'approved'
            #             approved_state = True
            #             approved_approval = True
            # else:
            #     price_status = 'no_price'
            # rec.price_status = price_status

    @api.depends('new_price', 'qty')
    def _compute_new_amount_total(self):
        for item in self:
            if item.compute_value > 0:
                item.new_amount_total = item.compute_value * item.new_price
            else:
                item.new_amount_total = item.new_price
