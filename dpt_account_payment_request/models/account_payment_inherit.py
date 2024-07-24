from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR
from datetime import datetime
from odoo.exceptions import ValidationError


class AccountPaymentType(models.Model):
    _name = 'dpt.account.payment.type'

    name = fields.Char(string='Name')
    rule_ids = fields.One2many('dpt.account.payment.type.rule', 'type_id', string='Rules')


class AccountPaymentTypeRule(models.Model):
    _name = 'dpt.account.payment.type.rule'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=1)
    department_id = fields.Many2one('hr.department', string='Department Request')
    type_id = fields.Many2one('dpt.account.payment.type')
    user_id = fields.Many2one('res.users', string='User Approve')
    type_compare = fields.Selection([('higher', 'Higher'),
                                     ('equal', 'Equal'),
                                     ('lower', 'Lower')], string='Type Compare', default='equal')
    value_compare = fields.Float(string='Value Compare')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    code = fields.Char(string='Payment Code', default='NEW', copy=False, index=True, tracking=True)
    user_id = fields.Many2one('res.users', string='User Request', default=lambda self: self.env.user, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department Request', tracking=True)
    type_id = fields.Many2one('dpt.account.payment.type', string='Type Request')
    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    approval_id = fields.Many2one('approval.request', string='Approval Payment Request')
    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='Status approval', default="new", related="approval_id.request_status")
    service_sale_ids = fields.Many2many('dpt.sale.service.management', string='Sale line')
    from_po = fields.Boolean()
    from_so = fields.Boolean()
    payment_user_type = fields.Selection([
        ('customer', 'Khách hàng'),
        ('company', 'Công ty'),
    ], string='Bên thanh toán')
    payment_user = fields.Selection([
        ('ltv', 'LTV'),
        ('dpt', 'DPT'),
    ], string='Pháp nhân thanh toán')
    active = fields.Boolean(default=True )

    def send_payment_request_request(self):
        category_id = self.env['approval.category'].search([('sequence_code', '=', 'DNTT')])
        if not category_id:
            raise ValidationError(_("Please config category approval change price (DNTT)"))
        create_values = {
            'request_owner_id': self.env.user.id,
            'category_id': category_id.id,
            'sale_id': self.id,
            'date': datetime.now(),
        }
        if self.sale_id:
            create_values.update({

            })
        approval_id = self.env['approval.request'].create(create_values)
        list_approver = self._compute_approver_list()
        if list_approver:
            approval_id.approver_ids = None
            approval_id.approver_ids = list_approver
        approval_id.action_confirm()
        self.approval_id = approval_id
        view_id = self.env.ref('approvals.approval_request_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'name': _('Approval request'),
            'view_mode': 'form',
            'res_id': approval_id.id,
            'views': [[view_id, 'form']],
        }

    def _compute_approver_list(self):
        list_approver = []
        list_exist = []
        for rec in self:
            for r in rec.type_id.rule_ids:
                if r.user_id.id in list_exist:
                    continue
                diff_value = rec.amount
                if r.type_compare == 'equal' and diff_value == 0:
                    required = True
                elif r.type_compare == 'higher' and diff_value > 0 and diff_value >= r.value_compare:
                    required = True
                elif r.type_compare == 'lower' and diff_value < 0 and abs(diff_value) >= r.value_compare:
                    required = True
                else:
                    required = False
                if not required:
                    continue
                list_approver.append((0, 0, {
                    'sequence': r.sequence,
                    'user_id': r.user_id.id,
                    'required': required
                }))
                list_exist.append(r.user_id.id)
        return list_approver

    @api.onchange('user_id')
    def onchange_user_get_department(self):
        self.department_id = self.user_id.department_id

    def _generate_account_code(self):
        sequence = self.env['ir.sequence'].next_by_code('account.payment') or '00'
        return f'{sequence}'

    @api.model
    def create(self, vals):
        if vals.get('code', 'NEW') == 'NEW':
            vals['code'] = self._generate_account_code()
        return super(AccountPayment, self).create(vals)
