from odoo import models, fields, api, _


class CreditHistory(models.Model):
    _name = 'dpt.credit.history'
    _description = 'Customer Credit History'
    _order = 'date desc'
    _rec_name = 'display_name'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade'
    )

    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True
    )

    action = fields.Selection([
        ('created', 'Credit Limit Created'),
        ('updated', 'Credit Limit Updated'),
        ('approved', 'Credit Approved'),
        ('rejected', 'Credit Rejected'),
        ('suspended', 'Credit Suspended'),
        ('reactivated', 'Credit Reactivated'),
        ('blocked', 'Credit Blocked'),
        ('interest_calculated', 'Interest Calculated')
    ], string='Action', required=True)

    old_credit_limit = fields.Monetary(
        string='Old Credit Limit',
        currency_field='currency_id'
    )

    new_credit_limit = fields.Monetary(
        string='New Credit Limit',
        currency_field='currency_id'
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )

    notes = fields.Text(string='Notes')

    currency_id = fields.Many2one(
        'res.currency',
        related='partner_id.currency_id',
        store=True
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name'
    )

    approval_request_id = fields.Many2one(
        'approval.request',
        string='Approval Request'
    )

    @api.depends('partner_id', 'action', 'date')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.partner_id.name} - {record.action} - {record.date.strftime('%Y-%m-%d %H:%M')}"
