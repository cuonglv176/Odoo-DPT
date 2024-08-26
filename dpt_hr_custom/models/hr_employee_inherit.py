from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    code = fields.Char('Code')
    dpt_level = fields.Selection([
        ('l1', 'L1'),
        ('l2', 'L2'),
        ('l3', 'L3'),
        ('l4', 'L4'),
        ('l5', 'L5')
    ], default='l1', string='Cấp bậc')



class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    code = fields.Char('Code', related='employee_id.code', compute_sudo=True)
    dpt_level = fields.Selection([
        ('l1', 'L1'),
        ('l2', 'L2'),
        ('l3', 'L3'),
        ('l4', 'L4'),
        ('l5', 'L5')
    ], default='l1', string='Cấp bậc', related='employee_id.dpt_level', compute_sudo=True)
