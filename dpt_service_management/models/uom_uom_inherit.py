from odoo import models, fields, api, _
from datetime import datetime


class UomUom(models.Model):
    _inherit = 'uom.uom'

    description = fields.Html(string='Description')
