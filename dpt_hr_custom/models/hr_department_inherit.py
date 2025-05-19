from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _rec_name = 'name'

    code = fields.Char('Code')


