# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, _, api


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
    
    def write(self, vals):
        """Ghi đè phương thức write để xử lý thay đổi trạng thái phê duyệt"""
        result = super(ApprovalRequest, self).write(vals)
        
        # Nếu trạng thái thay đổi, cập nhật dòng tờ khai liên quan
        if 'request_status' in vals and self.export_import_line_id:
            status = vals['request_status']
            
            # Nếu phê duyệt được chấp nhận
            if status == 'approved':
                self.export_import_line_id.sudo().action_approve_price()
                
            # Nếu phê duyệt bị từ chối
            elif status == 'refused':
                self.export_import_line_id.sudo().action_reject_price()
                
            # Nếu phê duyệt bị hủy và dòng tờ khai đang chờ phê duyệt
            elif status == 'cancel' and self.export_import_line_id.price_status == 'pending_approval':
                self.export_import_line_id.sudo().write({
                    'price_status': 'proposed',
                    'dpt_actual_price': self.export_import_line_id.dpt_system_price
                })
                self.export_import_line_id.message_post(
                    body=_("Yêu cầu phê duyệt đã bị hủy. Giá XHĐ quay về giá hệ thống.")
                )
        
        return result
    
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