from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    price_status = fields.Selection([
        ('no_price', 'No Price'),
        ('wait_approve', 'Wait Approve'),
        ('approved', 'Approved'),
    ], string='Status', default='no_price', compute="_compute_price_status")
    new_price = fields.Monetary(currency_field='currency_id', string='New Price')
    new_amount_total = fields.Monetary(currency_field='currency_id', string="New Amount Total",
                                       compute="_compute_new_amount_total")
    approval_id = fields.Many2one('approval.request', string='Approval Change Price')
    is_edit_new_price = fields.Boolean(string='Edit new price', compute="_compute_is_edit_new_price", default=False)

    def action_create_or_open_approval_request(self):
        view_form_id = self.env.ref('approvals.approval_request_view_form').id
        if self.approval_id:
            return {
                'name': "Đề nghị thanh toán",
                'type': 'ir.actions.act_window',
                'res_model': 'approval.request',
                'target': 'curent',
                'res_id': self.approval_id.id,
                'view_id': view_form_id,
                'view_mode': 'form',
            }
        request_approve = self.env['approval.category'].search([('sequence_code', '=', 'DNTT')])
        if not request_approve:
            raise ValidationError('Không tìm thấy loại phê duyệt')
        values_create = {
            'request_owner_id': self.env.user.id,
            'category_id': request_approve.id,
            'amount': self.amount_total,
            'date_confirmed': self.sale_id.date_order,
            'sale_id': self.sale_id.id
        }
        approval_request_id = self.env['approval.request'].create(values_create)
        self.approval_id = approval_request_id.id
        return {
            'name': "Đề nghị thanh toán",
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'target': 'curent',
            'res_id': approval_request_id.id,
            'view_id': view_form_id,
            'view_mode': 'form',
        }

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

    @api.depends('approval_id', 'approval_id.request_status')
    def _compute_price_status(self):
        for rec in self:
            if rec.approval_id:
                not_approved = rec.approval_id.filtered(lambda approval: approval.request_status in ('pending', 'new'))
                if not_approved:
                    price_status = 'wait_approve'
                else:
                    latest_approved = max(rec.approval_id, key=lambda line: line.date)

                    if latest_approved.request_status in ('refused', 'cancel'):
                        price_status = 'no_price'
                    else:
                        price_status = 'approved'
            else:
                price_status = 'no_price'
            rec.price_status = price_status

    @api.depends('new_price', 'qty')
    def _compute_new_amount_total(self):
        for item in self:
            item.new_amount_total = item.qty * item.new_price
