from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    code = fields.Char('Code')


