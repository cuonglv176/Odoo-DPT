from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrJoB(models.Model):
    _inherit = 'hr.job'

    code = fields.Char('Code')

    def name_get(self):
        res = []
        for job in self:
            job_name = job.name or ''
            code = job.code and job.code or ''
            res.append((job.id, f"{code}-{job_name}"))
        return res

