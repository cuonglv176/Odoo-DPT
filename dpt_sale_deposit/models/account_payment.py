from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_id = fields.Many2one('sale.order', string='Sale Order Deposit')
