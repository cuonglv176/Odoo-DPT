# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    job_report_count = fields.Integer(string='Số báo cáo công việc', compute='_compute_job_report_count',
                                     help="Tổng số báo cáo công việc của nhân viên này.")
    
    def _compute_job_report_count(self):
        for employee in self:
            employee.job_report_count = self.env['dpt.job.report'].search_count([
                ('employee_id', '=', employee.id)
            ])
    
    def action_view_job_reports(self):
        self.ensure_one()
        
        return {
            'name': 'Báo cáo công việc',
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.job.report',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        } 