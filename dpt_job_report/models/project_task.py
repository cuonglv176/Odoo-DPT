# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    job_task_id = fields.Many2one('dpt.job.task', string='Công việc báo cáo',
                                 help="Liên kết đến công việc tương ứng trong module Báo cáo công việc.")
    
    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        return res
    
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        
        # Đồng bộ trạng thái sang job task
        if 'stage_id' in vals:
            for record in self.filtered(lambda t: t.job_task_id):
                stage = record.stage_id
                if stage and stage.state:
                    state_mapping = {
                        'draft': 'new',
                        'in_progress': 'in_progress',
                        'done': 'done',
                        'cancel': 'cancelled'
                    }
                    if stage.state in state_mapping:
                        record.job_task_id.state = state_mapping[stage.state]
                        
                        # Cập nhật ngày bắt đầu và kết thúc
                        if stage.state == 'in_progress' and not record.job_task_id.date_start:
                            record.job_task_id.date_start = fields.Datetime.now()
                        elif stage.state == 'done' and not record.job_task_id.date_end:
                            record.job_task_id.date_end = fields.Datetime.now()
                
        return res 