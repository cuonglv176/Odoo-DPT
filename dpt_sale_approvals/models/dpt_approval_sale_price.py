from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class DptApprovalSalePrice(models.Model):
    _name = 'dpt.approval.sale.price'

    service_id = fields.Many2one('dpt.service.management')
    sequence = fields.Integer(string='Sequence')
    user_id = fields.Many2one('res.users', string='User')
    type_condition = fields.Selection([('price', 'Price'),
                                       ('price_list', 'Price List'),
                                       ('other', 'Other')], string='Type', default='other')
    domain = fields.Text(default=[])

    @api.onchange('type_condition')
    def _onchange_type_condition(self):
        if not self.type_condition or self.type_condition == 'other':
            self.domain = False
