from odoo import models, fields, api, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    def _compute_display_name(self):
        res = super(HrDepartment, self)._compute_display_name()
        if self.env.context.get('dpt_sale_management', False):
            for record in self:
                record.display_name = record.name
        return res