from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrJoB(models.Model):
    _inherit = 'hr.job'
    _rec_name = 'display_name'

    code = fields.Char('Code')
    display_name = fields.Char('Display name', compute="_compute_display_name", store=True)
    parent_department_id = fields.Many2one('hr.department', string='Phòng')
    center_id = fields.Many2one('hr.department', string='Trung tâm')
    bod_code = fields.Char(string='Mã BOD')

    @api.onchange('department_id')
    def onchange_department_id(self):
        self.parent_department_id = self.department_id.parent_id

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code}-{rec.name}"

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
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        job = self.search(domain + args, limit=limit)
        return job.name_get()
