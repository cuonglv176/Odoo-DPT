# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.addons.project.models.project_task import CLOSED_STATES
from odoo.exceptions import UserError

class Task(models.Model):
    _inherit = 'project.task'

    priority_level = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
    ], string='Mức độ ưu tiên', default='medium', tracking=True)
    
    # Ẩn trường priority mặc định
    priority = fields.Selection(groups="base.group_no_one")
    
    # Các trường tạm thời cho dashboard
    date_begin = fields.Date(string='Từ ngày')
    date_end = fields.Date(string='Đến ngày')
    total_tasks = fields.Integer(string='Tổng công việc', compute='_compute_dashboard_data')
    in_progress_tasks = fields.Integer(string='Đang làm', compute='_compute_dashboard_data')
    done_tasks = fields.Integer(string='Đã xong', compute='_compute_dashboard_data')
    late_tasks = fields.Integer(string='Trễ', compute='_compute_dashboard_data')
    upcoming_task_ids = fields.Many2many('project.task', string='Công việc đến hạn', compute='_compute_dashboard_data')
    priority_task_ids = fields.Many2many('project.task', relation='project_task_priority_rel', 
                                        string='Công việc ưu tiên', compute='_compute_dashboard_data')
    
    def write(self, vals):
        """
        Ghi đè phương thức write để đảm bảo user_ids không bị thay đổi vô tình
        khi task được mở từ dashboard
        """
        # Xác định request có đến từ dashboard không
        from_dashboard = self.env.context.get('from_task_dashboard')
        
        # Nếu đến từ dashboard và có thay đổi user_ids mà không có flag đặc biệt
        if from_dashboard and 'user_ids' in vals and not self.env.context.get('force_user_ids_update'):
            # Loại bỏ user_ids khỏi vals để tránh cập nhật
            vals.pop('user_ids')
        
        return super(Task, self).write(vals)
    
    @api.onchange('project_id', 'stage_id')
    def _onchange_protect_user_ids(self):
        """
        Phương thức onchange để bảo vệ user_ids khỏi thay đổi khi đến từ dashboard
        """
        # Kiểm tra nếu context có nguồn gốc từ dashboard
        if self.env.context.get('from_task_dashboard') and self.id:
            # Lấy giá trị user_ids từ database thay vì từ context
            original_task = self.env['project.task'].sudo().browse(self.id)
            self.user_ids = original_task.user_ids
            
    @api.depends('date_begin', 'date_end', 'user_ids')
    def _compute_dashboard_data(self):
        for record in self:
            # Lấy tham số filter
            date_begin = record.date_begin
            date_end = record.date_end
            user_ids = record.user_ids and record.user_ids.ids or False
            
            # Tính toán thống kê
            stats = record.sudo().get_task_statistics(user_id=user_ids, date_from=date_begin, date_to=date_end)
            record.total_tasks = stats['total']
            record.in_progress_tasks = stats['in_progress']
            record.done_tasks = stats['done']
            record.late_tasks = stats['late']
            
            # Lấy danh sách công việc đến hạn và ưu tiên
            record.upcoming_task_ids = record.sudo().get_upcoming_tasks(limit=10, user_id=user_ids)
            record.priority_task_ids = record.sudo().get_priority_tasks(limit=10, user_id=user_ids)

    def get_task_statistics(self, user_id=None, date_from=None, date_to=None):
        """
        Phương thức để lấy thống kê công việc
        :param user_id: ID người dùng cần thống kê
        :param date_from: Ngày bắt đầu
        :param date_to: Ngày kết thúc
        :return: dict chứa các chỉ số thống kê
        """
        domain = [('active', '=', True)]
        
        if user_id:
            domain.append(('user_ids', 'in', user_id))
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
            
        if date_to:
            domain.append(('create_date', '<=', date_to))
            
        # Lấy tổng số công việc
        total_tasks = self.search_count(domain)
        
        # Công việc đang làm (không ở trạng thái đóng)
        closed_states = list(CLOSED_STATES.keys())
        in_progress_domain = domain + [('state', 'not in', closed_states)]
        in_progress_tasks = self.search_count(in_progress_domain)
        
        # Công việc đã xong
        done_domain = domain + [('state', '=', '1_done')]
        done_tasks = self.search_count(done_domain)
        
        # Công việc trễ hạn
        today = fields.Date.today()
        late_domain = domain + [
            ('date_deadline', '<', today),
            ('state', 'not in', closed_states),
        ]
        late_tasks = self.search_count(late_domain)
        
        return {
            'total': total_tasks,
            'in_progress': in_progress_tasks,
            'done': done_tasks,
            'late': late_tasks,
        }
        
    def get_upcoming_tasks(self, limit=5, user_id=None):
        """
        Lấy danh sách công việc sắp đến hạn
        :param limit: Số lượng công việc tối đa
        :param user_id: ID người dùng (nếu cần lọc)
        :return: Recordset các công việc
        """
        closed_states = list(CLOSED_STATES.keys())
        domain = [
            ('active', '=', True),
            ('date_deadline', '>=', fields.Date.today()),
            ('state', 'not in', closed_states),
        ]
        
        if user_id:
            domain.append(('user_ids', 'in', user_id))
            
        return self.search(domain, limit=limit, order='date_deadline asc')
        
    def get_priority_tasks(self, limit=5, user_id=None):
        """
        Lấy danh sách công việc ưu tiên cao
        :param limit: Số lượng công việc tối đa
        :param user_id: ID người dùng (nếu cần lọc)
        :return: Recordset các công việc
        """
        closed_states = list(CLOSED_STATES.keys())
        domain = [
            ('active', '=', True),
            ('priority_level', '=', 'high'),
            ('state', 'not in', closed_states),
        ]
        
        if user_id:
            domain.append(('user_ids', 'in', user_id))
            
        return self.search(domain, limit=limit, order='date_deadline asc, id desc')
        
    def action_create_default_task(self):
        """
        Phương thức để tạo một công việc mặc định
        - Ngày hoàn thành: hôm nay
        - Dự án: Mặc định
        - Người phụ trách: người dùng hiện tại
        """
        self.ensure_one()
        
        # Tìm dự án mặc định
        default_project = self.env.ref('dpt_project_task.default_project', False)
        if not default_project:
            default_project = self.env['project.project'].search([('name', '=', 'Mặc định')], limit=1)
            if not default_project:
                # Tạo dự án mặc định nếu chưa có
                default_project = self.env['project.project'].create({
                    'name': 'Mặc định',
                    'description': 'Dự án mặc định cho các công việc được tạo từ bảng điều khiển',
                    'privacy_visibility': 'portal',
                })
        
        # Mở form tạo công việc mới với dữ liệu điền sẵn
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_project_id': default_project.id,
                'default_user_ids': [(6, 0, [self.env.user.id])],
                'default_date_deadline': fields.Date.today(),
                'default_priority_level': 'medium',
                'force_user_ids_update': True,  # Thêm flag đặc biệt để cho phép cập nhật user_ids
            }
        }
        
    def action_view_all_tasks(self):
        """
        Xem tất cả công việc với bộ lọc hiện tại
        """
        self.ensure_one()
        domain = [('active', '=', True)]
        
        if self.user_ids:
            domain.append(('user_ids', 'in', self.user_ids.ids))
        
        if self.date_begin:
            domain.append(('create_date', '>=', self.date_begin))
            
        if self.date_end:
            domain.append(('create_date', '<=', self.date_end))
        
        # Tìm các task thỏa mãn điều kiện
        tasks = self.env['project.task'].search(domain)
        
        # Nếu chỉ có một task, mở thẳng form view với context tối giản
        if len(tasks) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'res_id': tasks.id,
                'view_mode': 'form',
                'views': [(False, 'form')],
                'context': {
                    'create': False,
                    'from_task_dashboard': True,
                },
                'target': 'current',
                'flags': {'mode': 'readonly'},  # Mở ở chế độ chỉ đọc ban đầu
            }
        
        # Nếu có nhiều task, mở tree view với context tối giản
        return {
            'name': _('Tất cả công việc'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'domain': [('id', 'in', tasks.ids)],
            'view_mode': 'tree,form,kanban',
            'context': {
                'create': False,
                'search_default_my_tasks': 0,
                'from_task_dashboard': True,
            },
            'target': 'current',
        }
        
    def action_view_in_progress_tasks(self):
        """
        Xem danh sách công việc đang làm
        """
        self.ensure_one()
        closed_states = list(CLOSED_STATES.keys())
        domain = [('active', '=', True), ('state', 'not in', closed_states)]
        
        if self.user_ids:
            domain.append(('user_ids', 'in', self.user_ids.ids))
        
        if self.date_begin:
            domain.append(('create_date', '>=', self.date_begin))
            
        if self.date_end:
            domain.append(('create_date', '<=', self.date_end))
        
        # Tìm các task thỏa mãn điều kiện
        tasks = self.env['project.task'].search(domain)
        
        # Nếu chỉ có một task, mở thẳng form view với context tối giản
        if len(tasks) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'res_id': tasks.id,
                'view_mode': 'form',
                'views': [(False, 'form')],
                'context': {
                    'create': False,
                    'from_task_dashboard': True,
                },
                'target': 'current',
                'flags': {'mode': 'readonly'},  # Mở ở chế độ chỉ đọc ban đầu
            }
        
        # Nếu có nhiều task, mở tree view với context tối giản
        return {
            'name': _('Công việc đang làm'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'domain': [('id', 'in', tasks.ids)],
            'view_mode': 'tree,form,kanban',
            'context': {
                'create': False,
                'search_default_my_tasks': 0,
                'from_task_dashboard': True,
            },
            'target': 'current',
        }
        
    def action_view_done_tasks(self):
        """
        Xem danh sách công việc đã hoàn thành
        """
        self.ensure_one()
        domain = [('active', '=', True), ('state', '=', '1_done')]
        
        if self.user_ids:
            domain.append(('user_ids', 'in', self.user_ids.ids))
        
        if self.date_begin:
            domain.append(('create_date', '>=', self.date_begin))
            
        if self.date_end:
            domain.append(('create_date', '<=', self.date_end))
        
        # Tìm các task thỏa mãn điều kiện
        tasks = self.env['project.task'].search(domain)
        
        # Nếu chỉ có một task, mở thẳng form view với context tối giản
        if len(tasks) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'res_id': tasks.id,
                'view_mode': 'form',
                'views': [(False, 'form')],
                'context': {
                    'create': False,
                    'from_task_dashboard': True,
                },
                'target': 'current',
                'flags': {'mode': 'readonly'},  # Mở ở chế độ chỉ đọc ban đầu
            }
        
        # Nếu có nhiều task, mở tree view với context tối giản
        return {
            'name': _('Công việc đã hoàn thành'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'domain': [('id', 'in', tasks.ids)],
            'view_mode': 'tree,form,kanban',
            'context': {
                'create': False,
                'search_default_my_tasks': 0,
                'from_task_dashboard': True,
            },
            'target': 'current',
        }
        
    def action_view_late_tasks(self):
        """
        Xem danh sách công việc trễ hạn
        """
        self.ensure_one()
        closed_states = list(CLOSED_STATES.keys())
        today = fields.Date.today()
        domain = [
            ('active', '=', True), 
            ('date_deadline', '<', today),
            ('state', 'not in', closed_states)
        ]
        
        if self.user_ids:
            domain.append(('user_ids', 'in', self.user_ids.ids))
        
        if self.date_begin:
            domain.append(('create_date', '>=', self.date_begin))
            
        if self.date_end:
            domain.append(('create_date', '<=', self.date_end))
        
        # Tìm các task thỏa mãn điều kiện
        tasks = self.env['project.task'].search(domain)
        
        # Nếu chỉ có một task, mở thẳng form view với context tối giản
        if len(tasks) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'res_id': tasks.id,
                'view_mode': 'form',
                'views': [(False, 'form')],
                'context': {
                    'create': False,
                    'from_task_dashboard': True,
                },
                'target': 'current',
                'flags': {'mode': 'readonly'},  # Mở ở chế độ chỉ đọc ban đầu
            }
        
        # Nếu có nhiều task, mở tree view với context tối giản
        return {
            'name': _('Công việc trễ hạn'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'domain': [('id', 'in', tasks.ids)],
            'view_mode': 'tree,form,kanban',
            'context': {
                'create': False,
                'search_default_my_tasks': 0,
                'from_task_dashboard': True,
            },
            'target': 'current',
        } 