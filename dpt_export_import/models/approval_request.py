# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ApprovalRequest(models.Model):
    """
    Kế thừa model approval.request để thêm liên kết với dòng tờ khai và xử lý
    các sự kiện phê duyệt giá.
    """
    _inherit = 'approval.request'
    
    export_import_line_id = fields.Many2one(
        'dpt.export.import.line',
        string='Dòng tờ khai',
        ondelete='cascade'
    )
    
    def action_approve(self, approver=None):
        """
        Ghi đè phương thức phê duyệt để xử lý khi phê duyệt yêu cầu giá.
        Khi yêu cầu được duyệt, cập nhật giá thực tế bằng giá mong muốn.
        """
        res = super(ApprovalRequest, self).action_approve(approver=approver)
        
        # Xử lý khi phê duyệt yêu cầu giá
        for request in self:
            if request.export_import_line_id:
                request.export_import_line_id.action_approve_price()
        
        return res
    
    def action_refuse(self, approver=None):
        """
        Ghi đè phương thức từ chối.
        Khi yêu cầu bị từ chối, không cần xử lý gì thêm vì giá thực tế vẫn giữ nguyên.
        """
        res = super(ApprovalRequest, self).action_refuse(approver=approver)
        
        # Không cần xử lý gì thêm khi từ chối, vì giá thực tế vẫn giữ nguyên
        # Trường dpt_price_unit sẽ được mở khóa thông qua attrs trong view
        
        return res
    
    def action_cancel(self):
        """
        Ghi đè phương thức hủy yêu cầu.
        Khi yêu cầu bị hủy, không cần xử lý gì thêm.
        """
        res = super(ApprovalRequest, self).action_cancel()
        
        # Không cần xử lý gì thêm khi hủy yêu cầu
        # Trường dpt_price_unit sẽ được mở khóa thông qua attrs trong view
        
        return res 