from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    code = fields.Char('Code')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for department in self:
            if self.env.context.get('only_department_name', False):
                department.complete_name = department.name
            else:
                if department.parent_id:
                    department.complete_name = '%s / %s' % (department.parent_id.complete_name, department.name)
                else:
                    department.complete_name = department.name


