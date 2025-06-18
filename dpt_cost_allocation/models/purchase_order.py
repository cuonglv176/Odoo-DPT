# -*- coding: utf-8 -*-
# Placeholder for future extensions on purchase order model.
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Trường tờ khai (được mở rộng đầy đủ ở Release 03).
    # Tạm thời thêm để phục vụ liên kết related trong dpt.cost.allocation.
    export_import_id = fields.Many2one(
        'dpt.export.import',
        string="Tờ khai",
        tracking=True,
        help="Tờ khai để phân bổ chi phí từ PO này.",
    )

    # Placeholder cho các tính năng tương lai (Release 03+)
    # Các trường, phương thức khác sẽ được bổ sung sau.

    # Fields and methods will be added in future releases.
    cost_allocation_ids = fields.One2many(
        'dpt.cost.allocation',
        'purchase_order_id',
        string="Lịch sử phân bổ"
    )

    cost_allocation_count = fields.Integer(
        compute='_compute_cost_allocation_count',
        string="Số lần phân bổ"
    )

    @api.depends('cost_allocation_ids')
    def _compute_cost_allocation_count(self):
        for record in self:
            record.cost_allocation_count = len(record.cost_allocation_ids)

    def action_calculate_allocated_cost(self):
        """Tính và phân bổ chi phí từ PO vào các dòng tờ khai liên quan."""
        self.ensure_one()
        
        # Đảm bảo PO ở trạng thái done
        if self.state != 'done':
            raise UserError(_(
                "Chỉ các Đơn mua hàng đã khoá (trạng thái done) mới được phân bổ chi phí."))
        
        # 1. Hủy các phân bổ cũ của PO
        existing_allocations = self.env['dpt.cost.allocation'].search([
            ('purchase_order_id', '=', self.id),
            ('state', '=', 'allocated')
        ])
        if existing_allocations:
            existing_allocations.write({'state': 'cancelled'})
       
        # 2. Lấy thông tin cần thiết
        export_import = self.export_import_id
        if not export_import:
            raise UserError(_("Vui lòng chọn Tờ khai để phân bổ chi phí."))

        lines_to_allocate = self.order_line.filtered('include_in_invoice_cost')
        if not lines_to_allocate:
            raise UserError(_("Vui lòng đánh dấu ít nhất một dòng 'Tính giá XHĐ'."))
            
        total_cost = sum(lines_to_allocate.mapped('price_subtotal3'))
        
        declaration_lines = export_import.line_ids
        if not declaration_lines:
            raise UserError(_("Tờ khai chưa có dòng chi tiết."))
            
        total_base_value = sum(declaration_lines.mapped('dpt_invoice_base_value'))

        if total_base_value <= 0:
            raise UserError(_("Tổng 'Trị giá tính phân bổ' của các dòng tờ khai phải > 0. Không thể phân bổ."))
            
        # 3. Tạo bản ghi phân bổ mới ở trạng thái nháp
        new_allocation = self.env['dpt.cost.allocation'].create({
            'purchase_order_id': self.id,
            'total_allocated_from_po': total_cost,
            'currency_id': self.currency_id.id,
            'state': 'draft',  # Đảm bảo state là draft
        })
        
        # 4. Tạo các dòng chi tiết
        alloc_line_vals = []
        for line in declaration_lines:
            ratio = line.dpt_invoice_base_value / total_base_value if total_base_value else 0
            allocated_cost = total_cost * ratio
            alloc_line_vals.append({
                'cost_allocation_id': new_allocation.id,
                'export_import_line_id': line.id,
                'allocated_amount': allocated_cost,
                'ratio': ratio,
            })
        created_lines = self.env['dpt.cost.allocation.line'].create(alloc_line_vals)
        
        # 5. Cập nhật trạng thái thành 'allocated' sau khi đã tạo các dòng chi tiết
        new_allocation.write({'state': 'allocated'})
        
        # Ghi log cho PO, Tờ khai và từng dòng tờ khai
        self.message_post(body=_(
            "Đã tính và phân bổ chi phí <b>%s</b> vào tờ khai <b>%s</b>." % (
                self.currency_id.round(total_cost), export_import.name)))
        export_import.message_post(body=_(
            "Nhận chi phí phân bổ <b>%s</b> từ đơn mua hàng <b>%s</b>." % (
                self.currency_id.round(total_cost), self.name)))
        for alloc in created_lines:
            alloc.export_import_line_id.message_post(body=_(
                "Nhận phân bổ <b>%s</b> (tỷ lệ %s%%) từ PO <b>%s</b>." % (
                    self.currency_id.round(alloc.allocated_amount),
                    round(alloc.ratio * 100, 2),
                    self.name)))
        
        return True

    def action_view_cost_allocations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lịch sử phân bổ'),
            'res_model': 'dpt.cost.allocation',
            'domain': [('id', 'in', self.cost_allocation_ids.ids)],
            'view_mode': 'tree,form',
        }

    def write(self, vals):
        """Override write to enforce allocation lifecycle when PO state changes.
        - If the PO is leaving 'purchase' state, cancel active cost allocations.
        - Post appropriate chatter messages on related records.
        """
        # Detect state change away from 'purchase'
        if 'state' in vals and vals['state'] != 'purchase':
            for po in self:
                # Cancel only active allocations
                allocations_to_cancel = po.cost_allocation_ids.filtered(lambda a: a.state == 'allocated')
                if allocations_to_cancel:
                    allocations_to_cancel.write({'state': 'cancelled'})

                    # Post log on the declaration (export_import_id) if available
                    if po.export_import_id:
                        po.export_import_id.message_post(body=_(
                            "Phân bổ chi phí từ PO <b>%s</b> đã được hủy do PO chuyển trạng thái." % po.name
                        ))
                    # Post log on each declaration line
                    for line in po.export_import_id.line_ids:
                        line.message_post(body=_(
                            "Chi phí phân bổ chung đã bị loại bỏ do trạng thái đơn mua hàng %s đã thay đổi." % po.name
                        ))
        # Proceed with normal write
        return super(PurchaseOrder, self).write(vals)
    
    def unlink(self):
        for po in self:
            if po.cost_allocation_ids:
                po.cost_allocation_ids.filtered(lambda a: a.state == 'allocated').write({'state': 'cancelled'})
                if po.export_import_id:
                    po.export_import_id.message_post(
                        body=_("Phân bổ chi phí từ PO <b>%s</b> đã được hủy do PO bị xóa." % po.name)
                    )
        return super(PurchaseOrder, self).unlink()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    include_in_invoice_cost = fields.Boolean(
        string="Tính giá XHĐ",
        default=False,
        copy=False,
        help="Tích vào để tính chi phí này vào giá trị phân bổ.",
    )

    def write(self, vals):
        """Prevent editing critical fields when allocations exist on parent PO.
        Fields guarded: price_unit, product_qty, include_in_invoice_cost, taxes_id
        """
        guarded_fields = {'price_unit', 'product_qty', 'include_in_invoice_cost', 'taxes_id'}
        if guarded_fields.intersection(vals.keys()):
            for line in self:
                has_allocation = self.env['dpt.cost.allocation'].search_count([
                    ('purchase_order_id', '=', line.order_id.id),
                    ('state', '=', 'allocated'),
                ])
                if has_allocation:
                    # Specific message when toggling include_in_invoice_cost
                    if 'include_in_invoice_cost' in vals:
                        raise UserError(_(
                            "Không thể thay đổi đánh dấu 'Tính giá XHĐ' vì PO đã phân bổ chi phí. "
                            "Vui lòng hủy hoặc tính lại phân bổ trước khi chỉnh sửa."
                        ))
                    else:
                        raise UserError(_(
                            "Không thể thay đổi giá trị dòng PO sau khi đã phân bổ chi phí. "
                            "Vui lòng hủy hoặc tính lại phân bổ trước khi chỉnh sửa."
                        ))
        return super(PurchaseOrderLine, self).write(vals) 