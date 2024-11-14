from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.osv import expression
import re

class PartnerRequiredField(models.Model):
    _name = 'dpt.partner.required.fields'
    _description = 'DPT Service Partner required fields'

    name = fields.Char(string='Name', tracking=True)
    description = fields.Text(string='Description', tracking=True)
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
        ('selection', 'Selection')
    ], string='Fields type', default='char', tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Unit', tracking=True)
    code = fields.Char(string='Mã')
    value_char = fields.Char(string='Value Char')
    value_integer = fields.Float(string='Value Integer')
    value_date = fields.Date(string='Value Date')
    selection_value_id = fields.Many2one('dpt.sale.order.fields.selection', string='Selection Value')
    partner_id = fields.Many2one('res.partner', string='Partner')
