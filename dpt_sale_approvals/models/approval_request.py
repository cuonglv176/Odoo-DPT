from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'approval_id', string='Sale Service')
    sale_fields_ids = fields.One2many('dpt.sale.order.fields', 'approval_id', string='Sale Order Fields')
    order_line_ids = fields.One2many('sale.order.line', 'approval_id', string='Sale Order Line')
    history_ids = fields.One2many('dpt.approval.request.sale.line.history', 'approval_id', string='Lịch sử')
    sequence_code = fields.Char(string="Code", related='category_id.sequence_code')
    active = fields.Boolean('Active', default=True)
    payment_id = fields.Many2one('account.payment', string='ĐNTT')
    payment_type_id = fields.Many2one('dpt.account.payment.type', related='payment_id.type_id', string='Loại yêu cầu')
    approver_ids = fields.One2many('approval.approver', 'request_id', string="Approvers", check_company=True,
                                   compute='_compute_approver_ids', store=True, readonly=False)
    pricelist_id = fields.Many2one('product.pricelist',string="Pricelist")

    @api.depends('category_id', 'request_owner_id')
    def _compute_approver_ids(self):
        for request in self:
            users_to_approver = {}
            for approver in request.approver_ids:
                users_to_approver[approver.user_id.id] = approver

            users_to_category_approver = {}
            for approver in request.category_id.approver_ids:
                users_to_category_approver[approver.user_id.id] = approver

            approver_id_vals = []

            if request.category_id.manager_approval and not request.payment_id.type_id.is_bypass:
                employee = self.env['hr.employee'].search([('user_id', '=', request.request_owner_id.id)], limit=1)
                if employee.parent_id.user_id:
                    manager_user_id = employee.parent_id.user_id.id
                    manager_required = request.category_id.manager_approval == 'required'
                    sequence = 9
                    # We set the manager sequence to be lower than all others (9) so they are the first to approve.
                    user = self.env['res.users'].browse(employee.parent_id.user_id.id)
                    if user.has_group('dpt_security.group_dpt_director'):
                        if request.payment_id.type_id.is_ke_toan_truong:
                            sequence = 80
                        else:
                            sequence = 90
                    if user.has_group('dpt_security.group_dpt_ke_toan_truong'):
                        if request.payment_id.type_id.is_ke_toan_truong:
                            sequence = 90
                        else:
                            sequence = 80
                    self._create_or_update_approver(manager_user_id, users_to_approver, approver_id_vals,
                                                    manager_required, sequence)
                    if manager_user_id in users_to_category_approver.keys():
                        users_to_category_approver.pop(manager_user_id)

            for user_id in users_to_category_approver:
                user = self.env['res.users'].browse(user_id)
                sequence = users_to_category_approver[user_id].sequence
                if user.has_group('dpt_security.group_dpt_director'):
                    if request.payment_id.type_id.is_ke_toan_truong:
                        sequence = 80
                    else:
                        sequence = 90
                if user.has_group('dpt_security.group_dpt_ke_toan_truong'):
                    if request.payment_id.type_id.is_ke_toan_truong:
                        sequence = 90
                    else:
                        sequence = 80
                self._create_or_update_approver(user_id, users_to_approver, approver_id_vals,
                                                users_to_category_approver[user_id].required, sequence)

            for current_approver in users_to_approver.values():
                # Reset sequence and required for the remaining approvers that are no (longer) part of the category approvers or managers.
                # Set the sequence of these manually added approvers to 1000, so that they always appear after the category approvers.
                self._update_approver_vals(approver_id_vals, current_approver, False, 1000)

            request.update({'approver_ids': approver_id_vals})

    @api.model
    def _create_or_update_approver(self, user_id, users_to_approver, approver_id_vals, required, sequence):
        if user_id not in users_to_approver.keys():
            user = self.env['res.users'].browse(user_id)
            if user.has_group('dpt_security.group_dpt_director'):
                sequence = 90
                required = True
            if user.has_group('dpt_security.group_dpt_ke_toan_truong'):
                sequence = 80
                required = True
            approver_id_vals.append(Command.create({
                'user_id': user_id,
                'status': 'new',
                'required': required,
                'sequence': sequence,
            }))
        else:
            current_approver = users_to_approver.pop(user_id)
            self._update_approver_vals(approver_id_vals, current_approver, required, sequence)

    @api.model
    def _update_approver_vals(self, approver_id_vals, approver, new_required, new_sequence):
        if approver.required != new_required or approver.sequence != new_sequence:
            approver_id_vals.append(Command.update(approver.id, {'required': new_required, 'sequence': new_sequence}))

    def action_approve(self, approver=None):
        res = super(ApprovalRequest, self).action_approve(approver)
        approver = self.approver_ids.filtered(lambda sp: sp.status == 'approved')
        # if not approver or len(approver) == 1:
        if self.sequence_code == 'BAOGIA':
            if self.request_status == 'approved':
                self.sale_id.price_status = 'approved'
                self = self.with_context({'final_approved': True})
                for sale_service_id in self.sale_service_ids:
                    sale_service_id.price = sale_service_id.new_price
                    sale_service_id.price_status = 'approved'
                for order_line_id in self.order_line_ids:
                    order_line_id.price_unit = order_line_id.new_price_unit
                for sale_service_id in self.sale_id.sale_service_ids:
                    if sale_service_id.price_status in ('quoted', 'calculated'):
                        sale_service_id.price_status = 'approved'
                a = 1
                for sale_service_id in self.sale_id.sale_service_ids:
                    if sale_service_id.price_status != 'approved':
                        a = 0
                if a == 1:
                    self.sale_id.state = 'sent'
                for order_line_id in self.order_line_ids:
                    order_line_id.price_unit = order_line_id.new_price_unit
        return res

    def action_refuse(self, approver=None):
        res = super(ApprovalRequest, self).action_refuse(approver)
        # approver = self.approver_ids.filtered(lambda sp: sp.status == 'refused')
        if self.sequence_code == 'BAOGIA':
            if self.request_status == 'refused':
                self.sale_id.price_status = 'no_price'
                for sale_service_id in self.sale_service_ids:
                    sale_service_id.new_price = sale_service_id.price
                    sale_service_id.price_status = 'refuse_quoted'
                for order_line_id in self.order_line_ids:
                    order_line_id.new_price_unit = sale_service_id.price_unit
        return res

    def action_confirm(self):
        # make sure that the manager is present in the list if he is required
        self.ensure_one()
        if self.category_id.manager_approval == 'required':
            employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
            if not employee.parent_id:
                raise UserError(
                    _('This request needs to be approved by your manager. There is no manager linked to your employee profile.'))
            if not employee.parent_id.user_id:
                raise UserError(
                    _('This request needs to be approved by your manager. There is no user linked to your manager.'))
            if not self.approver_ids.filtered(lambda a: a.user_id.id == employee.parent_id.user_id.id):
                raise UserError(
                    _('This request needs to be approved by your manager. Your manager is not in the approvers list.'))
        if len(self.approver_ids) < self.approval_minimum:
            raise UserError(_("You have to add at least %s approvers to confirm your request.", self.approval_minimum))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at lease one document."))

        approvers = self.approver_ids
        if self.approver_sequence:
            approvers = approvers.filtered(lambda a: a.status in ['new', 'pending', 'waiting']).sorted(
                lambda a: a.sequence)

            approvers[1:].sudo().write({'status': 'waiting'})
            approvers = approvers[0] if approvers and approvers[0].status != 'pending' else self.env[
                'approval.approver']
        else:
            approvers = approvers.filtered(lambda a: a.status == 'new').sorted(lambda a: a.sequence)

        approvers._create_activity()
        approvers.sudo().write({'status': 'pending'})
        self.sudo().write({'date_confirmed': fields.Datetime.now()})


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'
    _order = 'sequence'

    def write(self, vals):
        if 'user_id' in vals:
            user = self.env['res.users'].browse(vals.get('user_id'))
            if user.has_group('dpt_security.group_dpt_director'):
                if self.request_id.payment_id.type_id.is_ke_toan_truong:
                    sequence = 90
                else:
                    sequence = 80
                vals.update({
                    'sequence': sequence,
                    'required': True
                })
            if user.has_group('dpt_security.group_dpt_ke_toan_truong'):
                if self.request_id.payment_id.type_id.is_ke_toan_truong:
                    sequence = 80
                else:
                    sequence = 90
                vals.update({
                    'sequence': sequence,
                    'required': True
                })
        return super(ApprovalApprover, self).write(vals)

    @api.model
    def create(self, vals):
        if 'user_id' in vals:
            user = self.env['res.users'].browse(vals.get('user_id'))
            if user.has_group('dpt_security.group_dpt_director'):
                if self.request_id.payment_id.type_id.is_ke_toan_truong:
                    sequence = 90
                else:
                    sequence = 80
                vals.update({
                    'sequence': sequence,
                    'required': True
                })
            if user.has_group('dpt_security.group_dpt_ke_toan_truong'):
                if self.request_id.payment_id.type_id.is_ke_toan_truong:
                    sequence = 80
                else:
                    sequence = 90
                vals.update({
                    'sequence': sequence,
                    'required': True
                })
        return super(ApprovalApprover, self).create(vals)
