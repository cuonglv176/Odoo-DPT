# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class JobReportSelfEvaluateWizard(models.TransientModel):
    _name = 'dpt.job.report.self.evaluate.wizard'
    _description = 'Tự đánh giá báo cáo công việc'

    report_id = fields.Many2one('dpt.job.report', string='Báo cáo', required=True,
                              readonly=True, ondelete='cascade')
    employee_id = fields.Many2one(related='report_id.employee_id', string='Nhân viên', readonly=True)
    date_from = fields.Date(related='report_id.date_from', string='Từ ngày', readonly=True)
    date_to = fields.Date(related='report_id.date_to', string='Đến ngày', readonly=True)
    
    completion_rate = fields.Float(related='report_id.completion_rate', string='Tỷ lệ hoàn thành (%)', readonly=True)
    on_time_rate = fields.Float(related='report_id.on_time_rate', string='Tỷ lệ đúng hạn (%)', readonly=True)
    
    self_evaluation = fields.Text(string='Tự đánh giá', required=True,
                                help="Hãy tự đánh giá kết quả công việc của bạn trong kỳ báo cáo này.")
    self_comment = fields.Text(string='Góp ý/Kiến nghị',
                             help="Bạn có thể ghi các góp ý, kiến nghị, khó khăn gặp phải, hoặc đề xuất cải tiến.")
    
    def action_confirm(self):
        """Xác nhận tự đánh giá"""
        self.ensure_one()
        self.report_id.write_self_evaluation(self.self_evaluation, self.self_comment)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tự đánh giá báo cáo'),
                'message': _('Đã lưu tự đánh giá của bạn.'),
                'sticky': False,
                'type': 'success',
            }
        } 