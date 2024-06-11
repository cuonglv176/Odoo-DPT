from odoo import models, fields, api, _


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

    @api.depends('approval_id')
    def _compute_is_edit_new_price(self):
        for rec in self:
            is_edit_new_price = False
            if rec.approval_id:
               for approver_id in rec.approval_id.approver_ids:
                   if self.env.user.id == approver_id.user_id.id:
                       is_edit_new_price = True
            rec.is_edit_new_price = is_edit_new_price

    @api.depends('approval_id')
    def _compute_price_status(self):
        for rec in self:
            if rec.approval_id:
                not_approved = rec.approval_id.filtered(lambda approval: approval.request_status != 'approved')
                if not_approved:
                    price_status = 'wait_approve'
                else:
                    price_status = 'approved'
            else:
                price_status = 'no_price'
            rec.price_status = price_status

    @api.depends('new_price', 'qty')
    def _compute_new_amount_total(self):
        for item in self:
            item.new_amount_total = item.qty * item.new_price
