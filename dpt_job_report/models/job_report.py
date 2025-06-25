# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import calendar


class JobReport(models.Model):
    _name = 'dpt.job.report'
    _description = 'Báo cáo công việc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'

    name = fields.Char(string='Tên báo cáo', required=True, copy=False, readonly=True, 
                       default=lambda self: _('New'),
                       help="Mã báo cáo công việc, được tạo tự động theo quy tắc đánh số.")
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True,
                                 default=lambda self: self.env.user.employee_id.id,
                                 tracking=True,
                                 help="Nhân viên làm báo cáo công việc này. Báo cáo sẽ chỉ hiển thị công việc của nhân viên này.")
    job_id = fields.Many2one('hr.job', string='Vị trí công việc', related='employee_id.job_id',
                            store=True, readonly=True,
                            help="Vị trí công việc của nhân viên, được lấy tự động từ thông tin nhân viên.")
    department_id = fields.Many2one('hr.department', string='Phòng ban', 
                                   related='employee_id.department_id', store=True, readonly=True,
                                   help="Phòng ban của nhân viên, được lấy tự động từ thông tin nhân viên.")
    date_from = fields.Date(string='Từ ngày', required=True, 
                           default=lambda self: date(fields.Date.today().year, fields.Date.today().month, 1),
                           help="Ngày bắt đầu của khoảng thời gian báo cáo, mặc định là ngày đầu tháng hiện tại.")
    date_to = fields.Date(string='Đến ngày', required=True, 
                         default=lambda self: (date(fields.Date.today().year, fields.Date.today().month, 1) + relativedelta(months=1, days=-1)),
                         help="Ngày kết thúc của khoảng thời gian báo cáo, mặc định là ngày cuối tháng hiện tại.")
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('self_evaluation', 'Tự đánh giá'),
        ('confirmed', 'Đã xác nhận'),
        ('evaluated', 'Đã đánh giá')
    ], string='Trạng thái', default='draft', tracking=True,
       help="Trạng thái của báo cáo: Nháp (đang làm), Tự đánh giá (nhân viên tự đánh giá), Đã xác nhận (chờ quản lý đánh giá), hoặc Đã đánh giá (hoàn thành).")
    
    # Tự đánh giá của nhân viên
    self_evaluation = fields.Text(string='Tự đánh giá', tracking=True,
                                help="Nhân viên tự đánh giá kết quả công việc của mình trong kỳ báo cáo.")
    self_evaluation_date = fields.Datetime(string='Ngày tự đánh giá', 
                                         readonly=True, copy=False,
                                         help="Thời điểm nhân viên tự đánh giá.")
    self_comment = fields.Text(string='Góp ý/Kiến nghị', tracking=True,
                             help="Nhân viên có thể ghi các góp ý, kiến nghị, khó khăn gặp phải, hoặc đề xuất cải tiến.")
    
    # Đánh giá của quản lý
    manager_evaluation = fields.Text(string='Đánh giá của quản lý', tracking=True,
                                   help="Đánh giá của quản lý về kết quả công việc trong kỳ báo cáo.")
    evaluation_user_id = fields.Many2one('res.users', string='Người đánh giá',
                                       readonly=True, copy=False,
                                       help="Người quản lý đã đánh giá báo cáo này.")
    evaluation_date = fields.Datetime(string='Ngày đánh giá', 
                                    readonly=True, copy=False,
                                    help="Thời điểm báo cáo được đánh giá.")
    manager_comment = fields.Text(string='Nhận xét của quản lý', tracking=True,
                                help="Quản lý có thể ghi nhận xét, đề xuất cải tiến, hoặc gợi ý phát triển cho nhân viên.")
    
    job_task_ids = fields.One2many('dpt.job.task', 'report_id', string='Công việc tự tạo',
                                  help="Danh sách các công việc do người dùng tự tạo hoặc được giao.")
    system_task_ids = fields.One2many('dpt.system.task', 'report_id', string='Công việc hệ thống',
                                     help="Danh sách công việc được hệ thống tạo tự động dựa trên dữ liệu nghiệp vụ.")
    
    # Computed fields for dashboard
    completion_rate = fields.Float(string='Tỷ lệ hoàn thành (%)', compute='_compute_performance_metrics', store=True,
                                  help="Tỷ lệ phần trăm công việc đã hoàn thành so với tổng số công việc.")
    avg_processing_time = fields.Float(string='Th.gian xử lý TB (giờ)', compute='_compute_performance_metrics', store=True,
                                      help="Thời gian trung bình để hoàn thành một công việc, tính bằng giờ.")
    on_time_rate = fields.Float(string='Tỷ lệ đúng hạn (%)', compute='_compute_performance_metrics', store=True,
                               help="Tỷ lệ phần trăm công việc hoàn thành đúng hoặc trước hạn.")
    
    # Counts for smart buttons
    job_task_count = fields.Integer(string='SL công việc tự tạo', compute='_compute_task_counts',
                                   help="Số lượng công việc tự tạo trong báo cáo này.")
    system_task_count = fields.Integer(string='SL công việc hệ thống', compute='_compute_task_counts',
                                      help="Số lượng công việc hệ thống trong báo cáo này.")
    
    # Các trường mới cho báo cáo tổng quan
    ongoing_task_count = fields.Integer(string='SL đang làm', compute='_compute_task_status_counts',
                                       help="Số lượng công việc đang thực hiện.")
    completed_task_count = fields.Integer(string='SL đã xong', compute='_compute_task_status_counts',
                                         help="Số lượng công việc đã hoàn thành.")
    overdue_task_count = fields.Integer(string='SL trễ', compute='_compute_task_status_counts',
                                       help="Số lượng công việc đã quá hạn chưa hoàn thành.")
    
    # Các trường danh sách công việc theo nhóm
    upcoming_task_ids = fields.Many2many('dpt.job.task', compute='_compute_task_groups',
                                        string='Công việc đến hạn',
                                        help="Danh sách công việc có thời hạn gần đến.")
    today_tasks_ids = fields.Many2many('dpt.job.task', compute='_compute_task_groups',
                                      string='Công việc phát sinh',
                                      relation='job_report_task_today_rel',
                                      help="Danh sách công việc phát sinh trong ngày.")
                                      
    # Trường ảo cho thống kê trạng thái - thay đổi thành Char để lưu JSON
    status_stats_json = fields.Char(string='Dữ liệu thống kê', compute='_compute_status_stats')
    
    # Trường để hiển thị bảng thống kê
    status_new_count = fields.Integer(string='Số lượng mới', compute='_compute_status_stats')
    status_in_progress_count = fields.Integer(string='Số lượng đang làm', compute='_compute_status_stats')
    status_done_count = fields.Integer(string='Số lượng hoàn thành', compute='_compute_status_stats')
    status_cancelled_count = fields.Integer(string='Số lượng đã hủy', compute='_compute_status_stats')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('dpt.job.report') or _('New')
        return super(JobReport, self).create(vals)
    
    @api.model
    def _create_monthly_reports(self):
        """
        Phương thức cron để tự động tạo báo cáo hàng tháng cho tất cả nhân viên
        Chạy vào ngày đầu tiên của mỗi tháng
        """
        today = fields.Date.today()
        # Chỉ chạy vào ngày đầu tiên của tháng
        if today.day != 1:
            return
            
        # Ngày đầu tháng
        first_day = date(today.year, today.month, 1)
        # Ngày cuối tháng
        last_day = (first_day + relativedelta(months=1, days=-1))
        
        # Lấy tất cả nhân viên đang hoạt động
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        reports_created = 0
        for employee in employees:
            # Kiểm tra xem đã có báo cáo cho tháng này chưa
            existing_report = self.search([
                ('employee_id', '=', employee.id),
                ('date_from', '=', first_day),
                ('date_to', '=', last_day)
            ], limit=1)
            
            if not existing_report:
                # Tạo báo cáo mới
                self.create({
                    'employee_id': employee.id,
                    'date_from': first_day,
                    'date_to': last_day,
                    'state': 'draft'
                })
                reports_created += 1
        
        return _("Đã tạo %s báo cáo tháng %s/%s") % (reports_created, today.month, today.year)
    
    @api.depends('job_task_ids', 'system_task_ids')
    def _compute_task_counts(self):
        for record in self:
            record.job_task_count = len(record.job_task_ids)
            record.system_task_count = len(record.system_task_ids)
    
    @api.depends('job_task_ids.state', 'job_task_ids.deadline')
    def _compute_task_status_counts(self):
        for record in self:
            # Đếm số lượng đang thực hiện
            record.ongoing_task_count = len(record.job_task_ids.filtered(lambda t: t.state == 'in_progress'))
            
            # Đếm số lượng đã hoàn thành
            record.completed_task_count = len(record.job_task_ids.filtered(lambda t: t.state == 'done'))
            
            # Đếm số lượng trễ (có deadline, chưa hoàn thành, và đã quá hạn)
            today = fields.Date.today()
            record.overdue_task_count = len(record.job_task_ids.filtered(
                lambda t: t.deadline and t.deadline.date() < today and t.state not in ['done', 'cancelled']
            ))
    
    @api.depends('job_task_ids', 'job_task_ids.deadline', 'job_task_ids.create_date')
    def _compute_task_groups(self):
        for record in self:
            # Lấy các công việc đến hạn (deadline trong vòng 3 ngày tới, chưa hoàn thành)
            today = fields.Date.today()
            upcoming_date = today + timedelta(days=3)
            
            record.upcoming_task_ids = record.job_task_ids.filtered(
                lambda t: t.deadline and t.deadline.date() <= upcoming_date and t.state not in ['done', 'cancelled']
            )
            
            # Lấy các công việc phát sinh được tạo hôm nay
            today_start = datetime.combine(today, datetime.min.time())
            record.today_tasks_ids = record.job_task_ids.filtered(
                lambda t: t.create_date and t.create_date >= today_start
            )
    
    @api.depends('job_task_ids.state')
    def _compute_status_stats(self):
        """Tính toán thống kê số lượng công việc theo trạng thái"""
        for record in self:
            # Đếm theo trạng thái
            record.status_new_count = len(record.job_task_ids.filtered(lambda t: t.state == 'new'))
            record.status_in_progress_count = len(record.job_task_ids.filtered(lambda t: t.state == 'in_progress'))
            record.status_done_count = len(record.job_task_ids.filtered(lambda t: t.state == 'done'))
            record.status_cancelled_count = len(record.job_task_ids.filtered(lambda t: t.state == 'cancelled'))
            
            # Lưu dữ liệu dưới dạng JSON
            import json
            record.status_stats_json = json.dumps({
                'new': record.status_new_count,
                'in_progress': record.status_in_progress_count,
                'done': record.status_done_count,
                'cancelled': record.status_cancelled_count
            })
    
    @api.depends('job_task_ids.state', 'system_task_ids.state', 
                'job_task_ids.date_start', 'job_task_ids.date_end',
                'job_task_ids.deadline')
    def _compute_performance_metrics(self):
        for record in self:
            # Tính tỷ lệ hoàn thành
            total_tasks = len(record.job_task_ids) + len(record.system_task_ids)
            if total_tasks:
                completed_tasks = len(record.job_task_ids.filtered(lambda t: t.state == 'done'))
                completed_tasks += len(record.system_task_ids.filtered(lambda t: t.state == 'done'))
                record.completion_rate = (completed_tasks / total_tasks) * 100
            else:
                record.completion_rate = 0
            
            # Tính thời gian xử lý trung bình
            processing_times = []
            for task in record.job_task_ids.filtered(lambda t: t.state == 'done' and t.date_start and t.date_end):
                processing_times.append((task.date_end - task.date_start).total_seconds() / 3600.0)  # Giờ
                
            record.avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Tính tỷ lệ đúng hạn
            tasks_with_deadline = record.job_task_ids.filtered(lambda t: t.state == 'done' and t.deadline)
            if tasks_with_deadline:
                on_time = len(tasks_with_deadline.filtered(lambda t: t.date_end and t.date_end <= t.deadline))
                record.on_time_rate = (on_time / len(tasks_with_deadline)) * 100
            else:
                record.on_time_rate = 0
    
    def action_confirm(self):
        self.state = 'confirmed'
    
    def action_draft(self):
        self.state = 'draft'
    
    def action_to_self_evaluation(self):
        """Chuyển trạng thái sang tự đánh giá"""
        self.state = 'self_evaluation'
        
    def action_self_evaluate(self):
        """Hiển thị form tự đánh giá"""
        self.ensure_one()
        return {
            'name': _('Tự đánh giá báo cáo'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.job.report.self.evaluate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_report_id': self.id,
            },
        }
        
    def action_evaluate(self):
        """Hiển thị form đánh giá của quản lý"""
        self.ensure_one()
        return {
            'name': _('Đánh giá báo cáo'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.job.report.evaluate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_report_id': self.id,
                'default_self_evaluation': self.self_evaluation,
                'default_self_comment': self.self_comment,
            },
        }
    
    def write_self_evaluation(self, self_evaluation, self_comment):
        """Ghi nhận tự đánh giá từ nhân viên"""
        self.ensure_one()
        self.write({
            'self_evaluation': self_evaluation,
            'self_comment': self_comment,
            'self_evaluation_date': fields.Datetime.now(),
            'state': 'confirmed'
        })
    
    def write_evaluation(self, manager_evaluation, manager_comment):
        """Ghi nhận đánh giá từ quản lý"""
        self.ensure_one()
        self.write({
            'manager_evaluation': manager_evaluation,
            'manager_comment': manager_comment,
            'evaluation_user_id': self.env.user.id,
            'evaluation_date': fields.Datetime.now(),
            'state': 'evaluated'
        })
    
    def action_view_job_tasks(self):
        self.ensure_one()
        return {
            'name': _('Công việc tự tạo'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.job.task',
            'view_mode': 'tree,form',
            'domain': [('report_id', '=', self.id)],
            'context': {'default_report_id': self.id},
        }
    
    def action_view_system_tasks(self):
        self.ensure_one()
        return {
            'name': _('Công việc hệ thống'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.system.task',
            'view_mode': 'tree,form',
            'domain': [('report_id', '=', self.id)],
            'context': {'default_report_id': self.id},
        }
    
    def action_compute_system_tasks(self):
        """Tính toán và tạo các công việc từ hệ thống"""
        self.ensure_one()
        
        # Chỉ áp dụng cho nhân viên CS trong giai đoạn 1
        if self.department_id.name != 'Customer Service':
            return
            
        # Xóa các công việc hệ thống cũ
        self.system_task_ids.unlink()
        
        # 1. Đơn hàng cần thanh toán (có phiếu hạch toán draft)
        payment_needed = self.env['sale.order'].search([
            ('employee_cs', '=', self.employee_id.id),
            ('invoice_status', '=', 'to invoice'),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to)
        ])
        
        for order in payment_needed:
            self.env['dpt.system.task'].create({
                'report_id': self.id,
                'name': _('Cần thanh toán cho %s') % order.name,
                'type': 'payment',
                'reference_model': 'sale.order',
                'reference_id': order.id,
                'state': 'open',
                'date_start': fields.Datetime.now(),
            })
        
        # 2. Đơn hàng chưa xếp xe (phiếu vận chuyển có trạng thái "Nháp")
        sale_orders = self.env['sale.order'].search([
            ('employee_cs', '=', self.employee_id.id),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to)
        ])
        
        # Kiểm tra xem có trường dpt_shipping_slip_ids không
        has_shipping_slip = hasattr(self.env['sale.order'], 'dpt_shipping_slip_ids')
        
        for order in sale_orders:
            # Chỉ xử lý nếu có trường dpt_shipping_slip_ids
            if has_shipping_slip and hasattr(order, 'dpt_shipping_slip_ids') and order.dpt_shipping_slip_ids:
                # Lọc các phiếu vận chuyển ở trạng thái "Nháp"
                draft_shipping_slips = order.dpt_shipping_slip_ids.filtered(
                    lambda slip: slip.cn_vehicle_stage_id.name == 'Nháp'
                )
                
                if draft_shipping_slips:
                    self.env['dpt.system.task'].create({
                        'report_id': self.id,
                        'name': _('Cần xếp xe cho %s') % order.name,
                        'type': 'shipping',
                        'reference_model': 'sale.order',
                        'reference_id': order.id,
                        'state': 'open',
                        'date_start': fields.Datetime.now(),
                    })
        
        # 3. Đơn hàng chưa giao (phiếu vận chuyển không ở trạng thái "Nháp" nhưng chưa giao thành công)
        for order in sale_orders:
            # Chỉ xử lý nếu có trường dpt_shipping_slip_ids
            if has_shipping_slip and hasattr(order, 'dpt_shipping_slip_ids') and order.dpt_shipping_slip_ids:
                # Lọc các phiếu vận chuyển không ở trạng thái "Nháp" và chưa giao
                undelivered_slips = order.dpt_shipping_slip_ids.filtered(
                    lambda slip: slip.cn_vehicle_stage_id.name != 'Nháp' and not slip.is_delivered
                )
                
                if undelivered_slips:
                    self.env['dpt.system.task'].create({
                        'report_id': self.id,
                        'name': _('Đang chờ giao hàng cho %s') % order.name,
                        'type': 'delivery',
                        'reference_model': 'sale.order',
                        'reference_id': order.id,
                        'state': 'open',
                        'date_start': fields.Datetime.now(),
                    })
        
        # 4. Đơn hàng chưa xuất hóa đơn
        uninvoiced_orders = self.env['sale.order'].search([
            ('employee_cs', '=', self.employee_id.id),
            ('invoice_status', '=', 'to invoice'),
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to)
        ])
        
        for order in uninvoiced_orders:
            self.env['dpt.system.task'].create({
                'report_id': self.id,
                'name': _('Cần xuất hóa đơn cho %s') % order.name,
                'type': 'invoice',
                'reference_model': 'sale.order',
                'reference_id': order.id,
                'state': 'open',
                'date_start': fields.Datetime.now(),
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Công việc hệ thống'),
                'message': _('Đã tạo %s công việc hệ thống.') % len(self.system_task_ids),
                'sticky': False,
                'type': 'success',
            }
        } 