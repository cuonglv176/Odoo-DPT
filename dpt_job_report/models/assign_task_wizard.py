# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class AssignTaskWizard(models.TransientModel):
    _name = 'dpt.assign.task.wizard'
    _description = 'Công cụ giao việc'

    name = fields.Char(string='Tên công việc', required=True,
                      help="Tên công việc cần giao cho nhân viên.")
    description = fields.Text(string='Mô tả chi tiết',
                             help="Mô tả chi tiết về công việc, yêu cầu và kết quả mong đợi.")
    priority = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Bình thường'),
        ('2', 'Cao'),
        ('3', 'Khẩn cấp')
    ], string='Độ ưu tiên', default='1',
       help="Mức độ ưu tiên của công việc, giúp nhân viên sắp xếp công việc theo thứ tự quan trọng.")
    deadline = fields.Datetime(string='Thời hạn',
                              help="Thời hạn hoàn thành công việc.")
    employee_id = fields.Many2one('hr.employee', string='Giao cho', required=True,
                                 help="Nhân viên được giao thực hiện công việc này.")
    
    def action_assign_task(self):
        """Tạo công việc và gán cho nhân viên được chọn"""
        self.ensure_one()
        
        # Tìm báo cáo hiện tại của nhân viên
        today = fields.Date.today()
        report = self.env['dpt.job.report'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
            ('state', '=', 'draft')
        ], limit=1)
        
        # Nếu không có báo cáo, tạo báo cáo mới
        if not report:
            report = self.env['dpt.job.report'].create({
                'name': _('Báo cáo cho %s') % self.employee_id.name,
                'employee_id': self.employee_id.id,
                'date_from': today,
                'date_to': today + timedelta(days=6),
                'state': 'draft'
            })
        
        # Tạo công việc
        task = self.env['dpt.job.task'].create({
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'deadline': self.deadline,
            'report_id': report.id,
            'source': 'assigned',
            'assigned_by': self.env.user.employee_id.id,
        })
        
        # Gửi thông báo cho nhân viên
        if self.employee_id.user_id:
            task.message_subscribe(partner_ids=[self.employee_id.user_id.partner_id.id])
            task.message_post(
                body=_('Bạn được giao một công việc mới bởi %s') % self.env.user.name,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[self.employee_id.user_id.partner_id.id]
            )
            
            # Tạo activity cho nhân viên
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
            summary = _('Công việc mới được giao: %s') % self.name
            note = self.description or _('Bạn được giao một công việc mới')
            
            self.env['mail.activity'].create({
                'activity_type_id': activity_type_id,
                'summary': summary,
                'note': note,
                'user_id': self.employee_id.user_id.id,
                'res_id': task.id,
                'res_model_id': self.env.ref('dpt_job_report.model_dpt_job_task').id,
                'date_deadline': self.deadline or fields.Date.today() + timedelta(days=3),
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã giao việc'),
                'message': _('Công việc "%s" đã được giao cho %s') % (self.name, self.employee_id.name),
                'sticky': False,
                'type': 'success',
            }
        } 