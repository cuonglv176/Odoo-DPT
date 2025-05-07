from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    payment_id = fields.Many2one('account.payment', string='ĐNTT')
    payment_due = fields.Datetime(string='Thời hạn thanh toán', related='payment_id.payment_due', store=True)
