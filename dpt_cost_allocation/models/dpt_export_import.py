# -*- coding: utf-8 -*-
# Placeholder for future extensions on dpt.export.import model.
from odoo import models, fields, api, _

# ------------------------------------------------
# Bổ sung các hàm compute và logic trên model dpt.export.import và dpt.export.import.line

# -----------------------------------------------------------------------------
# Extension for dpt.export.import (Tờ khai)
# -----------------------------------------------------------------------------

class DptExportImport(models.Model):
    _inherit = 'dpt.export.import'

    # Relation ngược tới các bản ghi phân bổ để đếm số lần phân bổ
    cost_allocation_ids = fields.One2many(
        'dpt.cost.allocation',
        'export_import_id',
        string='Phân bổ chi phí',
        help="""
        Danh sách các phiếu phân bổ chi phí liên quan đến tờ khai này.
        
        Cách sử dụng:
        - Hiển thị tất cả các phân bổ chi phí từ các đơn mua hàng khác nhau
        - Dùng để theo dõi chi tiết các nguồn chi phí đã được phân bổ
        - Khi tờ khai bị xóa, tất cả các phân bổ sẽ bị hủy tự động
        """
    )

    cost_allocation_count = fields.Integer(
        string='Số lượt phân bổ',
        compute='_compute_cost_allocation_count',
        store=True,
        help="""
        Tổng số lượt phân bổ chi phí đến tờ khai này.
        
        Cách sử dụng:
        - Hiển thị số lượng phiếu phân bổ chi phí liên quan đến tờ khai
        - Dùng để nhanh chóng biết tờ khai đã nhận bao nhiêu lần phân bổ
        - Bao gồm cả các phân bổ đã hủy và đang có hiệu lực
        """
    )

    # ---------------------------------------------------------------------
    # COMPUTE METHODS
    # ---------------------------------------------------------------------

    @api.depends('cost_allocation_ids')
    def _compute_cost_allocation_count(self):
        for record in self:
            record.cost_allocation_count = len(record.cost_allocation_ids)

# -----------------------------------------------------------------------------
# Extension for dpt.export.import.line (Dòng tờ khai)
# -----------------------------------------------------------------------------

class DptExportImportLine(models.Model):
    _inherit = 'dpt.export.import.line'

    # Liên kết tới các dòng phân bổ chi phí
    cost_allocation_line_ids = fields.One2many(
        'dpt.cost.allocation.line',
        'export_import_line_id',
        string='Chi tiết phân bổ',
        help="""
        Danh sách chi tiết các phân bổ chi phí cho dòng tờ khai này.
        
        Cách sử dụng:
        - Hiển thị tất cả các dòng chi tiết phân bổ từ các đơn mua hàng khác nhau
        - Dùng để theo dõi các nguồn chi phí đã được phân bổ cho dòng này
        - Khi dòng tờ khai bị xóa, tất cả các phân bổ liên quan sẽ bị hủy
        """
    )

    # Trị giá dùng để tính tỉ lệ phân bổ
    dpt_invoice_base_value = fields.Monetary(
        string='Trị giá tính phân bổ',
        currency_field='currency_id',
        compute='_compute_dpt_invoice_base_value',
        store=True,
        help="""
        Trị giá dùng để tính tỉ lệ phân bổ chi phí từ đơn mua hàng vào tờ khai.

        Công thức tính: Giá trị cơ bản + Thuế NK (XHĐ) + Thuế khác (XHĐ)

        Cách sử dụng:
        - Trường này được hệ thống tự động tính toán
        - Giá trị này quyết định tỉ lệ phân bổ chi phí của dòng tờ khai
        - Nếu thay đổi các trường thành phần sau khi đã phân bổ chi phí, hệ thống sẽ cảnh báo và yêu cầu tính lại
        """
    )

    # Chi phí phân bổ chung đã nhận
    dpt_allocated_cost_general = fields.Monetary(
        string='Chi phí phân bổ chung',
        currency_field='currency_id',
        compute='_compute_dpt_allocated_cost_general',
        store=True,
        help="""
        Tổng chi phí phân bổ chung đã nhận từ các đơn mua hàng liên quan.

        Cách sử dụng:
        - Trường được tính tự động từ các phân bổ chi phí hiện có
        - Chỉ tính tổng từ các phân bổ có trạng thái 'Đã phân bổ'
        - Khi một phân bổ bị hủy, giá trị này sẽ tự động cập nhật lại
        """
    )

    # Chi phí phân bổ riêng đã nhận
    dpt_allocated_cost_specific = fields.Monetary(
        string='Chi phí phân bổ riêng',
        currency_field='currency_id',
        compute='_compute_dpt_allocated_cost_specific',
        store=True,
        help="""
        Tổng chi phí phân bổ riêng đã nhận từ các đơn mua hàng liên quan.

        Cách sử dụng:
        - Trường được tính tự động từ các phân bổ chi phí riêng hiện có
        - Chỉ tính tổng từ các phân bổ có trạng thái 'Đã phân bổ' và loại 'specific'
        - Khi một phân bổ bị hủy, giá trị này sẽ tự động cập nhật lại
        """
    )

    # ---------------------------------------------------------------------
    # COMPUTE METHODS
    # ---------------------------------------------------------------------

    @api.depends('dpt_basic_value', 'dpt_amount_tax_import_basic', 'dpt_amount_tax_other_basic')
    def _compute_dpt_invoice_base_value(self):
        """
        Tính toán trị giá dùng để phân bổ chi phí cho dòng tờ khai.
        
        Công thức: Giá trị cơ bản + Thuế NK (XHĐ) + Thuế khác (XHĐ)
        
        Trường này được sử dụng làm cơ sở để tính tỷ lệ phân bổ chi phí từ đơn mua hàng.
        """
        for rec in self:
            base = rec.dpt_basic_value or 0.0
            tax_import = rec.dpt_amount_tax_import_basic or 0.0
            tax_other = rec.dpt_amount_tax_other_basic or 0.0
            rec.dpt_invoice_base_value = base + tax_import + tax_other

    @api.depends('cost_allocation_line_ids.allocated_amount', 'cost_allocation_line_ids.cost_allocation_id.state', 'cost_allocation_line_ids.cost_allocation_id.allocation_type')
    def _compute_dpt_allocated_cost_general(self):
        """
        Tính tổng chi phí phân bổ chung đã nhận cho dòng tờ khai.
        
        Chỉ tính các dòng phân bổ có trạng thái 'allocated' và loại 'general'.
        Khi một phân bổ bị hủy (state = 'cancelled'), giá trị sẽ tự động cập nhật lại.
        """
        for line in self:
            general_allocated_lines = line.cost_allocation_line_ids.filtered(
                lambda l: l.cost_allocation_id.state == 'allocated' and 
                         (l.cost_allocation_id.allocation_type == 'general' or 
                          not l.cost_allocation_id.allocation_type)  # Hỗ trợ dữ liệu cũ
            )
            line.dpt_allocated_cost_general = sum(general_allocated_lines.mapped('allocated_amount'))

    @api.depends('cost_allocation_line_ids.allocated_amount', 'cost_allocation_line_ids.cost_allocation_id.state', 'cost_allocation_line_ids.cost_allocation_id.allocation_type')
    def _compute_dpt_allocated_cost_specific(self):
        """
        Tính tổng chi phí phân bổ riêng đã nhận cho dòng tờ khai.
        
        Chỉ tính các dòng phân bổ có trạng thái 'allocated' và loại 'specific'.
        Khi một phân bổ bị hủy (state = 'cancelled'), giá trị sẽ tự động cập nhật lại.
        """
        for line in self:
            specific_lines = line.cost_allocation_line_ids.filtered(
                lambda l: l.cost_allocation_id.state == 'allocated' and l.cost_allocation_id.allocation_type == 'specific'
            )
            line.dpt_allocated_cost_specific = sum(specific_lines.mapped('allocated_amount'))

    # ---------------------------------------------------------------------
    # ONCHANGE METHODS
    # ---------------------------------------------------------------------

    @api.onchange('dpt_basic_value', 'dpt_amount_tax_import_basic', 'dpt_amount_tax_other_basic')
    def _onchange_dpt_basic_value(self):
        """
        Hiển thị cảnh báo khi thay đổi giá trị thành phần của trị giá tính phân bổ sau khi đã phân bổ chi phí.
        
        Returns:
            dict: Cảnh báo cho người dùng nếu cần thiết
        """
        if self.state == 'eligible' and self.dpt_allocated_cost_general > 0:
            return {
                'warning': {
                    'title': _('Cảnh báo'),
                    'message': _('Trị giá tờ khai đã thay đổi sau khi phân bổ chi phí. Vui lòng tính lại.'),
                }
            }

    # ---------------------------------------------------------------------
    # OVERRIDES
    # ---------------------------------------------------------------------

    def unlink(self):
        """
        Ghi đè phương thức xóa để tự động hủy phân bổ khi dòng tờ khai bị xóa.
        
        Khi dòng tờ khai bị xóa và có chi phí phân bổ, các phân bổ liên quan sẽ bị hủy
        và ghi log vào tờ khai để theo dõi.
        
        Returns:
            bool: Kết quả từ phương thức unlink gốc
        """
        for line in self:
            # Nếu dòng có chi phí phân bổ (chung hoặc riêng) và thuộc một tờ khai
            if (line.dpt_allocated_cost_general > 0 or line.dpt_allocated_cost_specific > 0) and line.export_import_id:
                # Tìm các phân bổ liên quan đến dòng tờ khai này
                related_allocations = self.env['dpt.cost.allocation.line'].search([
                    ('export_import_line_id', '=', line.id),
                    ('cost_allocation_id.state', '=', 'allocated')
                ]).mapped('cost_allocation_id')
                
                if related_allocations:
                    related_allocations.write({'state': 'cancelled'})
                    line.export_import_id.message_post(
                        body=_("Phân bổ chi phí đã được hủy do dòng tờ khai bị xóa.")
                    )
        return super(DptExportImportLine, self).unlink()

