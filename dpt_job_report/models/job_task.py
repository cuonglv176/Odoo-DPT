# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class JobTask(models.Model):
    _name = 'dpt.job.task'
    _description = 'Công việc tự tạo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, deadline asc, id desc'

    name = fields.Char(string='Tên công việc', required=True, tracking=True,
                      help="Tên công việc cần thực hiện. Mô tả ngắn gọn mục tiêu cần đạt được.")
    report_id = fields.Many2one('dpt.job.report', string='Báo cáo', required=True, ondelete='cascade',
                               help="Báo cáo công việc mà công việc này thuộc về.")
    description = fields.Text(string='Mô tả chi tiết',
                             help="Mô tả chi tiết về công việc cần thực hiện, bao gồm các yêu cầu và kết quả mong đợi.")
    
    priority = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Bình thường'),
        ('2', 'Cao'),
        ('3', 'Khẩn cấp')
    ], string='Độ ưu tiên', default='1', tracking=True,
       help="Mức độ ưu tiên của công việc, dùng để sắp xếp danh sách công việc theo thứ tự quan trọng.")
    
    deadline = fields.Datetime(string='Hạn hoàn thành',
                              help="Thời hạn cần hoàn thành công việc. Hệ thống sẽ tính toán tỷ lệ công việc hoàn thành đúng hạn.")
    
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='new', tracking=True,
       help="Trạng thái của công việc: Mới, Đang thực hiện, Hoàn thành hoặc Đã hủy.")
    
    source = fields.Selection([
        ('self', 'Tự tạo'),
        ('assigned', 'Được giao')
    ], string='Nguồn gốc', default='self', required=True,
       help="Nguồn gốc công việc: Tự tạo (bởi nhân viên) hoặc Được giao (bởi người quản lý).")
    
    assigned_by = fields.Many2one('hr.employee', string='Người giao việc',
                                 help="Người giao công việc này (chỉ áp dụng cho công việc được giao).")
    project_task_id = fields.Many2one('project.task', string='Công việc dự án',
                                     help="Liên kết đến công việc tương ứng trong module Dự án.")
    
    date_start = fields.Datetime(string='Ngày bắt đầu',
                                help="Ngày bắt đầu thực hiện công việc.")
    date_end = fields.Datetime(string='Ngày kết thúc',
                              help="Ngày hoàn thành công việc.")
    
    # Liên kết ngược lại với báo cáo
    employee_id = fields.Many2one('hr.employee', related='report_id.employee_id', 
                                 string='Nhân viên', store=True, readonly=True,
                                 help="Nhân viên được giao thực hiện công việc này.")
    department_id = fields.Many2one('hr.department', related='report_id.department_id',
                                   string='Phòng ban', store=True, readonly=True,
                                   help="Phòng ban của nhân viên thực hiện.")
    
    @api.constrains('deadline')
    def _check_deadline(self):
        """Kiểm tra deadline không được trong quá khứ"""
        for task in self:
            if task.deadline and task.deadline < fields.Datetime.now():
                raise exceptions.ValidationError(_('Thời hạn không thể là ngày trong quá khứ'))
    
    @api.model
    def create(self, vals):
        res = super(JobTask, self).create(vals)
        
        # Tạo task trong project và liên kết
        if not res.project_task_id:
            project_task_vals = {
                'name': res.name,
                'description': res.description,
                'date_deadline': res.deadline,
                'job_task_id': res.id,
            }
            
            # Trong Odoo 17, user_id đã thay đổi thành user_ids (many2many)
            if res.report_id.employee_id.user_id:
                project_task_vals['user_ids'] = [(4, res.report_id.employee_id.user_id.id)]
                
            project_task = self.env['project.task'].create(project_task_vals)
            
            res.project_task_id = project_task.id
            
            # Cập nhật trạng thái ban đầu
            if res.state != 'new':
                res._update_project_task_state()
        
        return res
    
    def write(self, vals):
        res = super(JobTask, self).write(vals)
        
        # Đồng bộ trạng thái sang project task
        if 'state' in vals or 'name' in vals or 'description' in vals or 'deadline' in vals:
            for record in self:
                record._update_project_task_state()
                
        return res
    
    def _update_project_task_state(self):
        """Đồng bộ trạng thái với project task"""
        self.ensure_one()
        
        if not self.project_task_id:
            return
            
        # Cập nhật các trường cơ bản
        vals = {
            'name': self.name,
            'description': self.description,
            'date_deadline': self.deadline,
        }
        
        # Cập nhật task
        self.project_task_id.write(vals)
        
        # Cập nhật trạng thái riêng biệt để tránh lỗi khi thiết lập stage_id
        try:
            # Map dpt.job.task state to project.task.type name instead of state
            if self.state:
                state_mapping = {
                    'new': 'New',
                    'in_progress': 'In Progress',
                    'done': 'Done',
                    'cancelled': 'Cancelled'
                }
                stage = self.env['project.task.type'].search(
                    [('name', '=', state_mapping.get(self.state))], limit=1
                )
                if stage:
                    self.project_task_id.write({'stage_id': stage.id})
        except Exception as e:
            # Log error but continue without failing
            _logger.warning(f"Could not update project task stage: {str(e)}")
    
    def action_start(self):
        self.write({
            'state': 'in_progress',
            'date_start': fields.Datetime.now(),
        })
    
    def action_done(self):
        self.write({
            'state': 'done',
            'date_end': fields.Datetime.now(),
        })
    
    def action_cancel(self):
        self.write({
            'state': 'cancelled',
        })
    
    def action_reset(self):
        self.write({
            'state': 'new',
            'date_start': False,
            'date_end': False,
        }) 