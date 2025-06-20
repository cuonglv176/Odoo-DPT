# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
        help="""
        Mã định danh duy nhất của bản ghi phân bổ chi phí.
        
        Cách tạo mã:
        - Được tạo tự động theo mẫu "PB/[tên đơn mua hàng]/[ID]"
        - Không thể sửa đổi trực tiếp
        
        Cách sử dụng:
        - Dùng để xác định và theo dõi các phiếu phân bổ
        - Hiển thị trong báo cáo và tham chiếu trong hệ thống
        """
    )
    
    allocation_type = fields.Selection([
        ('general', 'Chi phí phân bổ chung'),
        ('specific', 'Chi phí phân bổ riêng')
    ], string='Loại phân bổ', default='general', required=True, tracking=True,
    help="""
    Xác định loại phân bổ chi phí:
    - Chi phí phân bổ chung: phân bổ vào trường chi phí phân bổ chung của dòng tờ khai
    - Chi phí phân bổ riêng: phân bổ vào trường chi phí phân bổ riêng của dòng tờ khai
    """)
    
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Đơn mua hàng",
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        help="""
        Đơn mua hàng được phân bổ chi phí vào tờ khai.
        
        Cách sử dụng:
        - Chọn đơn mua hàng đã được xác nhận (hoàn thành)
        - Chi phí sẽ được tính từ các dòng đơn hàng có đánh dấu 'Tính giá XHĐ'
        - Khi đơn mua hàng thay đổi trạng thái, các phân bổ liên quan có thể bị hủy
        """
    )

    export_import_id = fields.Many2one(
        related='purchase_order_id.export_import_id',
        string="Tờ khai",
        store=True,
        index=True,
        tracking=True,
        help="""
        Tờ khai nhận phân bổ chi phí từ đơn mua hàng.
        
        Cách sử dụng:
        - Được tự động lấy từ trường tờ khai của đơn mua hàng
        - Phải chọn tờ khai trong đơn mua hàng trước khi thực hiện phân bổ
        - Chi phí sẽ được phân bổ theo tỷ lệ đến các dòng của tờ khai này
        """
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
        help="""
        Loại tiền tệ sử dụng cho phân bổ chi phí.
        
        Cách sử dụng:
        - Mặc định là tiền tệ của công ty
        - Tất cả các giá trị tiền tệ trong phân bổ sẽ sử dụng loại tiền này
        - Nên nhất quán với tiền tệ của đơn mua hàng và tờ khai
        """
    )

    allocation_date = fields.Datetime(
        string="Ngày phân bổ",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="""
        Thời điểm thực hiện phân bổ chi phí từ đơn mua hàng vào tờ khai.
        
        Cách sử dụng:
        - Được tự động cập nhật khi thực hiện phân bổ
        - Dùng để theo dõi thứ tự thời gian của các lần phân bổ
        - Phân bổ mới nhất sẽ hiển thị đầu tiên trong danh sách
        """
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
        help="""
        Danh sách các dòng chi tiết của phiếu phân bổ chi phí.
        
        Cách sử dụng:
        - Mỗi dòng thể hiện chi tiết phân bổ cho một dòng tờ khai
        - Các dòng được tạo tự động khi thực hiện phân bổ từ đơn mua hàng
        - Số tiền phân bổ cho mỗi dòng dựa trên tỷ lệ của 'Trị giá tính phân bổ'
        """
    )

    note = fields.Text(
        string="Ghi chú", 
        tracking=True,
        help="""
        Thông tin bổ sung về phiếu phân bổ chi phí.
        
        Cách sử dụng:
        - Ghi chú lý do phân bổ hoặc thông tin cần thiết khác
        - Sử dụng để lưu trữ các thông tin không có trường riêng
        - Không ảnh hưởng đến tính toán của hệ thống
        """
    )
    
    @api.depends('purchase_order_id', 'allocation_date')
    def _compute_name(self):
        for record in self:
            if record.purchase_order_id and record.id:
                record.name = f"PB/{record.purchase_order_id.name or 'NEW'}/{record.id}"
            else:
                record.name = "Phân bổ mới"
    
    def action_view_purchase_order(self):
        """
        Mở form đơn mua hàng liên quan đến phiếu phân bổ chi phí.
        
        Returns:
            dict: Thông tin action chuyển đến form đơn mua hàng
        """
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
        """
        Mở form tờ khai nhận phân bổ chi phí.
        
        Returns:
            dict: Thông tin action chuyển đến form tờ khai
        """
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
        """
        Ngăn chặn việc chỉnh sửa phiếu phân bổ khi đã ở trạng thái 'allocated'.
        
        Args:
            vals (dict): Giá trị cần cập nhật
            
        Raises:
            UserError: Khi cố gắng sửa phiếu đã phân bổ (trừ khi thay đổi trạng thái)
            
        Returns:
            bool: Kết quả từ phương thức write gốc
        """
        for record in self:
            if record.state == 'allocated' and 'state' not in vals:
                raise UserError(_("Không thể chỉnh sửa phiếu phân bổ đã được xác nhận!"))
        return super().write(vals)
        
    def unlink(self):
        """
        Ngăn chặn việc xóa phiếu phân bổ khi đã ở trạng thái 'allocated'.
        
        Raises:
            UserError: Khi cố gắng xóa phiếu đã phân bổ
            
        Returns:
            bool: Kết quả từ phương thức unlink gốc
        """
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
        help="""
        Phiếu phân bổ chi phí mà dòng này thuộc về.
        
        Cách sử dụng:
        - Mỗi dòng chi tiết liên kết đến một phiếu phân bổ
        - Khi phiếu phân bổ bị hủy, các dòng chi tiết cũng sẽ mất hiệu lực
        - Dùng để theo dõi nguồn gốc của chi phí phân bổ
        """
    )

    export_import_line_id = fields.Many2one(
        'dpt.export.import.line',
        string="Dòng tờ khai",
        required=True,
        help="""
        Dòng tờ khai nhận phân bổ chi phí.
        
        Cách sử dụng:
        - Chọn dòng tờ khai cần phân bổ chi phí
        - Mỗi dòng tờ khai có thể nhận nhiều phân bổ từ các đơn mua hàng khác nhau
        - Chi phí phân bổ sẽ được cập nhật vào trường 'Chi phí phân bổ chung' của dòng tờ khai
        """
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
        help="""
        Loại tiền tệ được sử dụng cho phân bổ chi phí này.
        
        Cách sử dụng:
        - Được kế thừa từ tiền tệ của phiếu phân bổ
        - Đảm bảo tính nhất quán của đơn vị tiền tệ trong toàn bộ quá trình phân bổ
        - Dùng để hiển thị và tính toán giá trị phân bổ theo đúng đơn vị tiền tệ
        """
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
        Giá trị dùng để tính tỷ lệ phân bổ chi phí cho dòng tờ khai này.
        
        Cách tính:
        - Công thức: Giá trị cơ bản + Thuế NK (XHĐ) + Thuế khác (XHĐ)
        - Lấy từ trường 'Trị giá tính phân bổ' của dòng tờ khai
        
        Cách sử dụng:
        - Trường này được hiển thị cho mục đích tham khảo
        - Tỷ lệ phân bổ được tính dựa trên giá trị này
        - Thay đổi giá trị này sau khi phân bổ sẽ yêu cầu tính lại phân bổ
        """
    )

    @api.model
    def create(self, vals):
        """
        Ngăn chặn việc tạo dòng phân bổ mới cho phiếu đã xác nhận.
        
        Args:
            vals (dict): Giá trị để tạo bản ghi mới
            
        Raises:
            UserError: Khi cố gắng thêm dòng vào phiếu phân bổ đã xác nhận
            
        Returns:
            CostAllocationLine: Bản ghi mới được tạo
        """
        if vals.get('cost_allocation_id'):
            allocation = self.env['dpt.cost.allocation'].browse(vals['cost_allocation_id'])
            if allocation.state == 'allocated':
                raise UserError(_("Không thể thêm dòng phân bổ chi phí vào phiếu đã được xác nhận!"))
        return super().create(vals)
        
    def write(self, vals):
        """
        Ngăn chặn việc chỉnh sửa dòng phân bổ của phiếu đã xác nhận.
        
        Args:
            vals (dict): Giá trị cần cập nhật
            
        Raises:
            UserError: Khi cố gắng sửa dòng của phiếu đã xác nhận
            
        Returns:
            bool: Kết quả từ phương thức write gốc
        """
        for record in self:
            if record.cost_allocation_id.state == 'allocated':
                raise UserError(_("Không thể chỉnh sửa dòng phân bổ chi phí thuộc phiếu đã được xác nhận!"))
        return super().write(vals)
        
    def unlink(self):
        """
        Ngăn chặn việc xóa dòng phân bổ của phiếu đã xác nhận.
        
        Raises:
            UserError: Khi cố gắng xóa dòng của phiếu đã xác nhận
            
        Returns:
            bool: Kết quả từ phương thức unlink gốc
        """
        for record in self:
            if record.cost_allocation_id.state == 'allocated':
                raise UserError(_("Không thể xóa dòng phân bổ chi phí thuộc phiếu đã được xác nhận!"))
        return super().unlink() 