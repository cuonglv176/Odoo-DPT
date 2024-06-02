from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    code = fields.Char('Code')


