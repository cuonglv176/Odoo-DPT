# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SystemTask(models.Model):
    _name = 'dpt.system.task'
    _description = 'Công việc hệ thống'
    _order = 'date_start desc, id desc'

    report_id = fields.Many2one('dpt.job.report', string='Báo cáo', required=True, ondelete='cascade',
                               help="Báo cáo công việc mà công việc hệ thống này thuộc về.")
    name = fields.Char(string='Tên công việc', required=True,
                      help="Tên mô tả công việc hệ thống cần thực hiện.")
    
    type = fields.Selection([
        ('payment', 'Thanh toán'),
        ('shipping', 'Xếp xe'),
        ('delivery', 'Giao hàng'),
        ('invoice', 'Hóa đơn'),
        ('other', 'Khác')
    ], string='Loại công việc', required=True,
       help="Phân loại công việc hệ thống theo các nhóm chức năng khác nhau, giúp nhóm và lọc dữ liệu.")
    
    reference_model = fields.Char(string='Model tham chiếu', 
                                 help="Tên technical của model được tham chiếu (VD: sale.order, purchase.order).")
    reference_id = fields.Integer(string='ID tham chiếu',
                                 help="ID của bản ghi được tham chiếu.")
    
    state = fields.Selection([
        ('open', 'Đang mở'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='open',
       help="Trạng thái của công việc hệ thống: Đang mở, Hoàn thành hoặc Đã hủy.")
    
    date_start = fields.Datetime(string='Ngày bắt đầu',
                                help="Ngày tạo công việc hệ thống.")
    date_end = fields.Datetime(string='Ngày kết thúc',
                              help="Ngày hoàn thành công việc hệ thống.")
    
    # Liên kết ngược lại với báo cáo
    employee_id = fields.Many2one('hr.employee', related='report_id.employee_id', 
                                 string='Nhân viên', store=True, readonly=True,
                                 help="Nhân viên phụ trách công việc này.")
    
    # Trường mới để lưu trữ thông tin tham chiếu
    reference_name = fields.Char(string='Tham chiếu', compute='_compute_reference_name', store=True,
                                help="Tên hiển thị của bản ghi được tham chiếu.")
    
    @api.model
    def create(self, vals):
        """Automatically set date_start when creating new system tasks"""
        if not vals.get('date_start'):
            vals['date_start'] = fields.Datetime.now()
        return super(SystemTask, self).create(vals)
    
    @api.depends('reference_model', 'reference_id')
    def _compute_reference_name(self):
        """Tính toán tên tham chiếu"""
        for task in self:
            if task.reference_model and task.reference_id:
                try:
                    record = self.env[task.reference_model].browse(task.reference_id)
                    if record.exists():
                        task.reference_name = record.display_name
                    else:
                        task.reference_name = False
                except Exception:
                    task.reference_name = False
            else:
                task.reference_name = False
    
    def action_done(self):
        """Đánh dấu công việc hoàn thành"""
        self.write({
            'state': 'done',
            'date_end': fields.Datetime.now(),
        })
    
    def action_cancel(self):
        """Hủy công việc"""
        self.write({
            'state': 'cancelled',
        })
    
    def action_view_reference(self):
        """Xem bản ghi tham chiếu"""
        self.ensure_one()
        if not self.reference_model or not self.reference_id:
            return
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.reference_model,
            'res_id': self.reference_id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def auto_update_status(self):
        """Tự động cập nhật trạng thái của các công việc hệ thống"""
        # Cập nhật trạng thái cho các công việc thanh toán
        payment_tasks = self.search([
            ('type', '=', 'payment'),
            ('state', '=', 'open'),
            ('reference_model', '=', 'sale.order')
        ])
        
        for task in payment_tasks:
            order = self.env['sale.order'].browse(task.reference_id)
            if order.exists() and order.invoice_status != 'to invoice':
                task.action_done()
        
        # Cập nhật trạng thái cho các công việc xếp xe
        shipping_tasks = self.search([
            ('type', '=', 'shipping'),
            ('state', '=', 'open'),
            ('reference_model', '=', 'sale.order')
        ])
        
        for task in shipping_tasks:
            order = self.env['sale.order'].browse(task.reference_id)
            if order.exists():
                draft_shipping_slips = order.dpt_shipping_slip_ids.filtered(
                    lambda slip: slip.cn_vehicle_stage_id.name == 'Nháp'
                )
                if not draft_shipping_slips:
                    task.action_done()
        
        # Cập nhật trạng thái cho các công việc giao hàng
        delivery_tasks = self.search([
            ('type', '=', 'delivery'),
            ('state', '=', 'open'),
            ('reference_model', '=', 'sale.order')
        ])
        
        for task in delivery_tasks:
            order = self.env['sale.order'].browse(task.reference_id)
            if order.exists():
                undelivered_slips = order.dpt_shipping_slip_ids.filtered(
                    lambda slip: slip.cn_vehicle_stage_id.name != 'Nháp' and not slip.is_delivered
                )
                if not undelivered_slips:
                    task.action_done()
        
        # Cập nhật trạng thái cho các công việc xuất hóa đơn
        invoice_tasks = self.search([
            ('type', '=', 'invoice'),
            ('state', '=', 'open'),
            ('reference_model', '=', 'sale.order')
        ])
        
        for task in invoice_tasks:
            order = self.env['sale.order'].browse(task.reference_id)
            if order.exists() and order.invoice_status != 'to invoice':
                task.action_done()
        
        return True 