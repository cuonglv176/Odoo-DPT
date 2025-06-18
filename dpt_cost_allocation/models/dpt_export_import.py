# -*- coding: utf-8 -*-
# Placeholder for future extensions on dpt.export.import model.
from odoo import models, fields, api, _

# Release 04: Logic tính toán cho các trường mới
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
    )

    cost_allocation_count = fields.Integer(
        string='Số lượt phân bổ',
        compute='_compute_cost_allocation_count',
        store=True,
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

    # ---------------------------------------------------------------------
    # COMPUTE METHODS
    # ---------------------------------------------------------------------

    @api.depends('dpt_basic_value', 'dpt_amount_tax_import_basic', 'dpt_amount_tax_other_basic')
    def _compute_dpt_invoice_base_value(self):
        """Trị giá tính phân bổ = Giá trị cơ bản + Thuế NK (XHĐ) + Thuế khác (XHĐ)"""
        for rec in self:
            base = rec.dpt_basic_value or 0.0
            tax_import = rec.dpt_amount_tax_import_basic or 0.0
            tax_other = rec.dpt_amount_tax_other_basic or 0.0
            rec.dpt_invoice_base_value = base + tax_import + tax_other

    @api.depends('cost_allocation_line_ids.allocated_amount', 'cost_allocation_line_ids.cost_allocation_id.state')
    def _compute_dpt_allocated_cost_general(self):
        """Tổng hợp chi phí phân bổ chung còn hiệu lực (state == 'allocated')."""
        for line in self:
            allocated_lines = line.cost_allocation_line_ids.filtered(
                lambda l: l.cost_allocation_id.state == 'allocated'
            )
            line.dpt_allocated_cost_general = sum(allocated_lines.mapped('allocated_amount'))

    # ---------------------------------------------------------------------
    # ONCHANGE METHODS
    # ---------------------------------------------------------------------

    @api.onchange('dpt_basic_value', 'dpt_amount_tax_import_basic', 'dpt_amount_tax_other_basic')
    def _onchange_dpt_basic_value(self):
        """Cảnh báo khi trị giá tờ khai thay đổi sau khi đã có chi phí phân bổ."""
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
        """Tự động hủy phân bổ khi dòng tờ khai bị xóa."""
        for line in self:
            if line.dpt_allocated_cost_general > 0 and line.export_import_id:
                related_allocations = self.env['dpt.cost.allocation'].search([
                    ('export_import_id', '=', line.export_import_id.id),
                    ('state', '=', 'allocated')
                ])
                if related_allocations:
                    related_allocations.write({'state': 'cancelled'})
                    line.export_import_id.message_post(
                        body=_("Phân bổ chi phí đã được hủy do dòng tờ khai bị xóa.")
                    )
        return super(DptExportImportLine, self).unlink()

# end of file 