from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    code = fields.Char('Code')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    code = fields.Char('Code', related='employee_id.code', compute_sudo=True)
