from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.osv import expression
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_field_ids = fields.One2many('dpt.partner.required.fields', 'partner_id', string='Thông tin mẫu')
