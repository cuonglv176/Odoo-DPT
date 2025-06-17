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
            ('allocated', 'Đã phân bổ'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        default='allocated',
        required=True,
        tracking=True,
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

    allocated_amount = fields.Monetary(string="Số tiền phân bổ")

    currency_id = fields.Many2one(
        related='cost_allocation_id.currency_id',
        store=True,
    )

    ratio = fields.Float(string="Tỷ lệ", digits='Account') 