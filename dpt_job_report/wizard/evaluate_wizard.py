# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class JobReportEvaluateWizard(models.TransientModel):
    _name = 'dpt.job.report.evaluate.wizard'
    _description = 'Đánh giá báo cáo công việc'

    report_id = fields.Many2one('dpt.job.report', string='Báo cáo', required=True,
                              readonly=True, ondelete='cascade')
    employee_id = fields.Many2one(related='report_id.employee_id', string='Nhân viên', readonly=True)
    date_from = fields.Date(related='report_id.date_from', string='Từ ngày', readonly=True)
    date_to = fields.Date(related='report_id.date_to', string='Đến ngày', readonly=True)
    
    completion_rate = fields.Float(related='report_id.completion_rate', string='Tỷ lệ hoàn thành (%)', readonly=True)
    on_time_rate = fields.Float(related='report_id.on_time_rate', string='Tỷ lệ đúng hạn (%)', readonly=True)
    
    # Tự đánh giá của nhân viên (hiển thị để quản lý tham khảo)
    self_evaluation = fields.Text(string='Tự đánh giá của nhân viên', readonly=True)
    self_comment = fields.Text(string='Góp ý/Kiến nghị của nhân viên', readonly=True)
    
    # Đánh giá của quản lý
    manager_evaluation = fields.Text(string='Đánh giá của quản lý', required=True,
                                   help="Nhập đánh giá của bạn về kết quả công việc của nhân viên trong kỳ báo cáo này.")
    manager_comment = fields.Text(string='Nhận xét & Gợi ý', 
                                help="Nhập nhận xét, đề xuất cải tiến, hoặc gợi ý phát triển cho nhân viên.")
    
    def action_confirm(self):
        """Xác nhận đánh giá và ghi nhận vào báo cáo"""
        self.ensure_one()
        self.report_id.write_evaluation(self.manager_evaluation, self.manager_comment)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đánh giá báo cáo'),
                'message': _('Đã đánh giá báo cáo công việc của %s.') % self.employee_id.name,
                'sticky': False,
                'type': 'success',
            }
        } 