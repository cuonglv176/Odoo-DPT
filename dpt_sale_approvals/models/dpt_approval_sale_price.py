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
    type_compare = fields.Selection([('higher', 'Higher'),
                                     ('equal', 'Equal'),
                                     ('lower', 'Lower')], string='Type Compare', default='equal')
    type_value = fields.Selection([('numberic', 'Numberic'),
                                   ('rate', 'Rate %')], string='Type Value')
    value_compare = fields.Float(string='Value Compare')
