from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    code = fields.Char('Code')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for department in self:
            department.complete_name = department.name


