# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# This file will be populated in later releases. 

class CostAllocation(models.Model):
    """
    Lưu lại mỗi lần một PO thực hiện phân bổ chi phí cho một tờ khai.
    """

    _name = 'dpt.cost.allocation'
    _description = 'Bản ghi phân bổ chi phí PO-Tờ khai'
    _rec_name = 'name'
    _order = 'allocation_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Mã phân bổ",
        compute="_compute_name",
        store=True,
        copy=False,
        readonly=True,
    )
    
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Đơn mua hàng",
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )

    export_import_id = fields.Many2one(
        related='purchase_order_id.export_import_id',
        string="Tờ khai",
        store=True,
        index=True,
        tracking=True,
    )

    total_allocated_from_po = fields.Monetary(
        string="Tổng chi phí đã phân bổ",
        currency_field='currency_id',
        tracking=True,
        help="""
        Tổng chi phí từ đơn mua hàng sẽ được phân bổ cho tờ khai.

        Cách sử dụng:
        - Giá trị này được tính từ tổng các dòng đơn mua hàng có đánh dấu 'Tính giá XHĐ'
        - Đây là tổng số tiền sẽ được phân bổ cho các dòng tờ khai
        - Dùng để kiểm tra tổng giá trị phân bổ
        """
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    allocation_date = fields.Datetime(
        string="Ngày phân bổ",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ('draft', 'Nháp'),
            ('allocated', 'Đã phân bổ'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        default='draft',
        required=True,
        tracking=True,
        help="""
        Trạng thái của phiếu phân bổ chi phí.

        Các trạng thái:
        - Nháp: Phiếu mới tạo, chưa áp dụng phân bổ chi phí
        - Đã phân bổ: Phân bổ chi phí đã được áp dụng cho tờ khai
        - Đã hủy: Phân bổ chi phí đã được hủy, không còn hiệu lực

        Cách sử dụng:
        - Chỉ phiếu ở trạng thái 'Đã phân bổ' mới được tính vào chi phí phân bổ chung
        - Phiếu 'Đã phân bổ' không thể chỉnh sửa, chỉ có thể hủy
        - Khi hủy phân bổ, trường 'Chi phí phân bổ chung' trên dòng tờ khai sẽ tự động cập nhật
        """
    )

    line_ids = fields.One2many(
        'dpt.cost.allocation.line',
        'cost_allocation_id',
        string="Chi tiết phân bổ",
    )

    note = fields.Text(string="Ghi chú", tracking=True)
    
    @api.depends('purchase_order_id', 'allocation_date')
    def _compute_name(self):
        for record in self:
            if record.purchase_order_id and record.id:
                record.name = f"PB/{record.purchase_order_id.name or 'NEW'}/{record.id}"
            else:
                record.name = "Phân bổ mới"
    
    def action_view_purchase_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Đơn mua hàng'),
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
            'target': 'current',
        }
    
    def action_view_export_import(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tờ khai'),
            'res_model': 'dpt.export.import',
            'view_mode': 'form',
            'res_id': self.export_import_id.id,
            'target': 'current',
        }
        
    def action_cancel(self):
        """
        Huỷ phân bổ chi phí, thay đổi trạng thái từ 'allocated' thành 'cancelled'.
        - Chỉ có thể huỷ các phiếu phân bổ đang ở trạng thái 'Đã phân bổ'.
        - Ghi log cho các bản ghi liên quan.
        """
        for record in self:
            # Kiểm tra điều kiện
            if record.state != 'allocated':
                raise UserError(_("Chỉ được phép huỷ những phiếu phân bổ ở trạng thái 'Đã phân bổ'."))
                
            # Chuyển trạng thái
            record.write({'state': 'cancelled'})
            
            # Ghi log cho phiếu phân bổ
            record.message_post(body=_("Phiếu phân bổ chi phí đã được chuyển sang trạng thái 'Đã huỷ'."))
            
            # Ghi log cho đơn mua hàng
            if record.purchase_order_id:
                record.purchase_order_id.message_post(body=_(
                    "Phiếu phân bổ chi phí <b>%s</b> đã bị huỷ." % record.name
                ))
                
            # Ghi log cho tờ khai
            if record.export_import_id:
                record.export_import_id.message_post(body=_(
                    "Phiếu phân bổ chi phí <b>%s</b> từ đơn mua hàng <b>%s</b> đã bị huỷ." % (
                        record.name, record.purchase_order_id.name)
                ))
                
            # Ghi log cho từng dòng tờ khai
            for line in record.line_ids:
                if line.export_import_line_id:
                    line.export_import_line_id.message_post(body=_(
                        "Chi phí đã phân bổ (<b>%s</b>) từ PO <b>%s</b> đã bị huỷ." % (
                            record.currency_id.round(line.allocated_amount),
                            record.purchase_order_id.name)
                    ))
            
        return True

    def write(self, vals):
        for record in self:
            if record.state == 'allocated' and 'state' not in vals:
                raise UserError(_("Không thể chỉnh sửa phiếu phân bổ đã được xác nhận!"))
        return super().write(vals)
        
    def unlink(self):
        for record in self:
            if record.state == 'allocated':
                raise UserError(_("Không thể xóa phiếu phân bổ đã được xác nhận!"))
        return super().unlink()


class CostAllocationLine(models.Model):
    """
    Lưu chi tiết số tiền được phân bổ cho từng dòng tờ khai.
    """

    _name = 'dpt.cost.allocation.line'
    _description = 'Chi tiết phân bổ chi phí'

    cost_allocation_id = fields.Many2one(
        'dpt.cost.allocation',
        string="Bản ghi phân bổ",
        required=True,
        ondelete='cascade',
        index=True,
    )

    export_import_line_id = fields.Many2one(
        'dpt.export.import.line',
        string="Dòng tờ khai",
        required=True,
    )

    allocated_amount = fields.Monetary(
        string="Số tiền phân bổ",
        help="""
        Số tiền được phân bổ từ đơn mua hàng cho dòng tờ khai này.

        Cách tính:
        - Tổng chi phí phân bổ * Tỷ lệ phân bổ của dòng

        Cách sử dụng:
        - Trường này được hệ thống tự động tính toán khi phân bổ
        - Dùng để cập nhật giá trị chi phí phân bổ trên dòng tờ khai
        """
    )

    currency_id = fields.Many2one(
        related='cost_allocation_id.currency_id',
        store=True,
    )

    ratio = fields.Float(
        string="Tỷ lệ", 
        digits='Account',
        help="""
        Tỷ lệ phân bổ chi phí cho dòng tờ khai này.

        Cách tính:
        - Tỷ lệ = Trị giá tính phân bổ của dòng / Tổng trị giá tính phân bổ của tất cả các dòng
        - Giá trị hiển thị dạng phần trăm (%)

        Cách sử dụng:
        - Hệ thống tự động tính toán tỷ lệ này khi thực hiện phân bổ
        - Dùng để kiểm tra tính hợp lý của việc phân bổ chi phí
        """
    )
    
    line_invoice_base_value = fields.Monetary(
        string="Trị giá tính phân bổ",
        related='export_import_line_id.dpt_invoice_base_value',
        readonly=True,
        store=False,
        help="""
        Giá trị cơ bản để tính phân bổ chi phí từ dòng tờ khai liên kết.

        Cách sử dụng:
        - Giá trị này được lấy từ trường 'Trị giá tính phân bổ' của dòng tờ khai tương ứng
        - Dùng để xem nhanh cơ sở tính toán tỷ lệ phân bổ
        - Giá trị này chỉ để tham khảo và không thể sửa đổi trực tiếp trong form phân bổ
        """
    )

    @api.model
    def create(self, vals):
        if vals.get('cost_allocation_id'):
            allocation = self.env['dpt.cost.allocation'].browse(vals['cost_allocation_id'])
            if allocation.state == 'allocated':
                raise UserError(_("Không thể thêm dòng phân bổ chi phí vào phiếu đã được xác nhận!"))
        return super().create(vals)
        
    def write(self, vals):
        for record in self:
            if record.cost_allocation_id.state == 'allocated':
                raise UserError(_("Không thể chỉnh sửa dòng phân bổ chi phí thuộc phiếu đã được xác nhận!"))
        return super().write(vals)
        
    def unlink(self):
        for record in self:
            if record.cost_allocation_id.state == 'allocated':
                raise UserError(_("Không thể xóa dòng phân bổ chi phí thuộc phiếu đã được xác nhận!"))
        return super().unlink() 