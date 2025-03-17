from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    payment_id = fields.Many2one('account.payment', string='ĐNTT')
    is_payment_in_day = fields.Boolean(string='Thanh toán trong ngày',related='payment_id.is_payment_in_day')