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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if name:
            domain = ['|',  ('name', operator, name), ('code', operator, name)]
        job = self.search(domain + args, limit=limit)
        return job.name_get()
