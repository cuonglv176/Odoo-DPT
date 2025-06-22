# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
import math
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class DptExportImportLine(models.Model):
    _name = "dpt.export.import.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import line'

    name = fields.Text(string='Name', compute="_get_name")
    sequence = fields.Integer(default=1)
    export_import_id = fields.Many2one('dpt.export.import', string='Export import')
    lot_code = fields.Char(string='Lot code')
    sale_id = fields.Many2one('sale.order', string='Sale order', tracking=True)
    stock_picking_ids = fields.Many2many('stock.picking', string='Lot code',
                                         domain="[('id', 'in', available_picking_ids)]", tracking=True)
    available_picking_ids = fields.Many2many('stock.picking', string='Lot code',
                                             compute="_compute_domain_picking_package")
    sale_user_id = fields.Many2one('res.users', string='User Sale', compute="compute_sale_user")
    partner_id = fields.Many2one('res.partner', string='Sale Partner', related='sale_id.partner_id')
    sale_line_id = fields.Many2one('sale.order.line', string='Sale order line', domain=[('order_id', '=', 'sale_id')])
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id')
    product_id = fields.Many2one('product.product', string='Product', tracking=True)
    package_ids = fields.Many2many('purchase.order.line.package', string='Package',
                                   domain="[('id', 'in', available_package_ids)]")
    available_package_ids = fields.Many2many('purchase.order.line.package', string='Package',
                                             compute="_compute_domain_picking_package")
    dpt_english_name = fields.Char(string='English name', tracking=True)
    dpt_description = fields.Text(string='Description Product', size=240, tracking=True)
    dpt_n_w_kg = fields.Float(string='N.W (KG)', tracking=True)
    dpt_g_w_kg = fields.Float(string='G.W (KG)', tracking=True)
    dpt_uom_id = fields.Many2one('uom.uom', string='Uom Export/Import', tracking=True)
    dpt_uom2_ecus_id = fields.Many2one('uom.uom', string='ĐVT SL2 (Ecus)', tracking=True)
    dpt_uom2_id = fields.Many2one('uom.uom', string='ĐVT 2', tracking=True)
    dpt_price_kd = fields.Char(string='Giá KD/giá cũ', tracking=True)
    dpt_tax_import = fields.Float(string='Tax import (%)', tracking=True)
    dpt_amount_tax_import = fields.Monetary(string='Amount Tax Import', currency_field='currency_id',
                                            compute="_compute_dpt_amount_tax_import")
    dpt_tax_ecus5 = fields.Char(string='VAT ECUS5', tracking=True)
    dpt_tax = fields.Float(string='VAT(%)', tracking=True)
    dpt_amount_tax = fields.Monetary(string='Amount Tax', currency_field='currency_id',
                                     compute="_compute_dpt_amount_tax")
    dpt_amount_tax_import_basic = fields.Monetary(
        string='Tiền thuế NK (XHĐ)', 
        currency_field='currency_id',
        compute='_compute_basic_taxes', 
        store=True, 
        tracking=True
    )
    dpt_amount_tax_other_basic = fields.Monetary(
        string='Tiền thuế Khác (XHĐ)', 
        currency_field='currency_id',
        compute='_compute_basic_taxes', 
        store=True, 
        tracking=True
    )
    dpt_amount_tax_vat_basic = fields.Monetary(
        string='Tiền thuế VAT (XHĐ)', 
        currency_field='currency_id',
        compute='_compute_basic_taxes', 
        store=True, 
        tracking=True
    )
    dpt_total_tax_basic = fields.Monetary(
        string='Tổng thuế (XHĐ)', 
        currency_field='currency_id',
        compute='_compute_basic_taxes', 
        store=True, 
        tracking=True
    )
    dpt_exchange_rate = fields.Float(string='Tỉ giá HQ', tracking=True, currency_field='currency_id', store=True,
                                     digits=(12, 4), compute="_compute_dpt_exchange_rate")
    dpt_exchange_rate_basic = fields.Float(string='Tỉ giá XHĐ', tracking=True, currency_field='currency_id',
                                            store=True,
                                            digits=(12, 4))
    dpt_exchange_rate_basic_final = fields.Float(string='Tỷ giá NH (cuối cùng)', tracking=True, digits=(12, 4))
    dpt_basic_value = fields.Monetary(
        string='Giá trị cơ bản',
        currency_field='currency_id',
        compute='_compute_dpt_basic_value',
        store=True,
        tracking=True
    )
    hs_code_id = fields.Many2one('dpt.export.import.acfta', string='HS Code', tracking=True)
    dpt_code_hs = fields.Char(string='H')
    dpt_sl1 = fields.Float(string='SL1', tracking=True, digits=(12, 4))
    dpt_price_unit = fields.Monetary(string='Giá XHĐ mong muốn', tracking=True, currency_field='currency_id', store=True)
    dpt_uom1_id = fields.Many2one('uom.uom', string='ĐVT 1', tracking=True)
    dpt_sl2 = fields.Float(string='SL2', tracking=True, digits=(12, 4))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    currency_usd_id = fields.Many2one('res.currency', string='Currency USD', default=1)
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
    currency_krw_id = fields.Many2one('res.currency', string='Currency KRW', default=32)
    customs_price_type = fields.Selection([
        ('optimal', 'Tối ưu'),
        ('actual', 'Thực tế'),
        ('requested', 'Theo yêu cầu')
    ], string='Giá HQ', default='optimal', tracking=True,
        help="Loại giá khai báo hải quan: Tối ưu - giá tối ưu cho khai báo, Thực tế - giá thực tế, Theo yêu cầu - giá theo yêu cầu của khách hàng")
    dpt_price_usd = fields.Float(string='Giá khai (USD)', tracking=True, currency_field='currency_usd_id',
                                 digits=(12, 4))
    dpt_total_usd = fields.Monetary(string='Total (USD)', currency_field='currency_usd_id',
                                    compute="_compute_dpt_total_usd", digits=(12, 4))
    dpt_total_usd_vnd = fields.Monetary(string='Total USD (VND)', currency_field='currency_id',
                                        compute="_compute_dpt_total_usd_vnd")
    dpt_total_cny_vnd = fields.Monetary(string='Total CNY (VND)', currency_field='currency_id',
                                        compute="_compute_dpt_total_cny_vnd")
    dpt_price_cny_vnd = fields.Float(string='Price CNY (VND)', tracking=True, currency_field='currency_cny_id',
                                     digits=(12, 4))

    dpt_total_krw_vnd = fields.Monetary(string='Tổng KRW (VND)', currency_field='currency_krw_id',
                                        compute="_compute_dpt_total_krw_vnd")
    dpt_price_krw_vnd = fields.Float(string='Giá KRW (VND)', tracking=True, currency_field='currency_krw_id',
                                     digits=(12, 4))
    dpt_tax_other = fields.Float(string='Tax Other (%)', tracking=True)
    dpt_amount_tax_other = fields.Monetary(string='Amount Tax Other', currency_field='currency_id',
                                           compute="_compute_dpt_amount_tax_other")
    dpt_total_vat = fields.Monetary(string='Total VAT', tracking=True, compute="_compute_total_vat",
                                    currency_field='currency_id')
    dpt_total = fields.Monetary(string='Total', tracking=True, currency_field='currency_id')
    dpt_is_new = fields.Boolean(string='Is new', tracking=True, default=False)
    state = fields.Selection([
        ('draft', 'Nháp'),
        # ('draft_declaration', 'Tờ khai nháp'),
        ('wait_confirm', 'Chờ chứng từ phản hồi'),
        ('confirmed', 'Chứng từ phản hồi'),
        ('eligible', 'Đủ điều kiện khai báo'),
        # ('declared', 'Tờ khai thông quan'),
        # ('released', 'Giải phóng'),
        # ('consulted', 'Tham vấn'),
        # ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft', tracking=True)

    declaration_type = fields.Selection([
        ('usd', 'USD'),
        ('cny', 'CNY'),
        ('krw', 'KRW'),
    ], string='Declaration type', default='usd', tracking=True)
    product_history_id = fields.Many2one('dpt.export.import.line', string='Description Selection')
    is_readonly_item_description = fields.Boolean(string='Chỉ đọc item', default=False)
    item_description_vn = fields.Html(string='Tem XNK (VN)')
    item_description_en = fields.Html(string='Tem XNK (EN)')
    manufacturer = fields.Text(string='Nhà sản xuất', tracking=True)
    # dunghq
    brand = fields.Text(string='Nhãn hiệu(Cũ)', tracking=True)
    material = fields.Text(string='Chất liệu', tracking=True)
    risk_reason = fields.Selection([
        ('different_price', 'Giá khai khác'),
        ('same_model_different_price', 'Cùng model/nhãn hiệu khác giá'),
        ('no_invoice', 'Khách hàng có đơn hàng không lấy hóa đơn'),
    ], string='Lý do rủi ro', compute='_compute_risk_reason', store=True)
    brand_id = fields.Many2one('dpt.product.brand', string='Brand')
    model_id = fields.Many2one('dpt.product.model', string='Model')
    # dunghq
    model = fields.Text(string='Model(Cũ)', tracking=True)

    picking_count = fields.Integer('Picking Count', compute="_compute_picking_count")
    is_history = fields.Boolean(string='History', default=False, tracking=True)
    active = fields.Boolean('Active', default=True)

    # Allocated Cost Fields
    dpt_allocated_cost_general = fields.Monetary(
        string='Chi phí phân bổ chung',
        currency_field='currency_id',
        tracking=True
    )
    dpt_allocated_cost_specific = fields.Monetary(
        string='Chi phí phân bổ riêng',
        currency_field='currency_id',
        tracking=True
    )
    dpt_total_allocated_cost = fields.Monetary(
        string='Tổng chi phí phân bổ',
        currency_field='currency_id',
        compute='_compute_total_allocated_cost',
        store=True,
        tracking=True
    )

    # Cost Fields
    dpt_cost_of_goods = fields.Monetary(
        string='Giá vốn hàng hóa',
        currency_field='currency_id',
        compute='_compute_cost_of_goods',
        store=True,
        tracking=True
    )
    dpt_unit_cost = fields.Monetary(
        string='Đơn giá vốn',
        currency_field='currency_id',
        compute='_compute_unit_cost',
        store=True,
        tracking=True
    )

    # Price Approval Fields
    can_request_price_approval = fields.Boolean(
        string="Có thể yêu cầu phê duyệt giá",
        compute='_compute_can_request_price_approval'
    )
    dpt_price_min_allowed = fields.Monetary(
        string="Giá bán min cho phép",
        currency_field='currency_id',
        compute='_compute_allowed_prices',
        store=True,
        tracking=True
    )
    dpt_price_max_allowed = fields.Monetary(
        string="Giá bán max cho phép",
        currency_field='currency_id',
        compute='_compute_allowed_prices',
        store=True,
        tracking=True
    )
    dpt_system_price = fields.Monetary(
        string="Giá XHĐ hệ thống",
        currency_field='currency_id',
        compute='_compute_allowed_prices',
        store=True,
        tracking=True
    )
    dpt_actual_price = fields.Monetary(
        string="Giá XHĐ thực tế",
        currency_field='currency_id',
        tracking=True
    )
    approval_request_id = fields.Many2one(
        'approval.request',
        string="Yêu cầu phê duyệt",
        copy=False
    )
    approval_status = fields.Selection(
        related='approval_request_id.request_status',
        string="Trạng thái phê duyệt",
        store=True
    )
    price_revalidation_required = fields.Boolean(
        string="Cần định giá lại",
        default=False,
        copy=False
    )

    # Thêm các trường để hỗ trợ tính năng kiểm tra giá
    price_outside_range = fields.Boolean(string='Giá ngoài khoảng cho phép', default=False)
    price_temp = fields.Monetary(string='Giá tạm thời', currency_field='currency_id', store=False)

    # Thêm hai trường mới
    dpt_amount_tax_vat_customs = fields.Monetary(
        string='Tiền thuế VAT (HQ)',
        currency_field='currency_id',
        compute='_compute_tax_vat_customs', 
        store=True, 
        tracking=True
    )
    dpt_amount_tax_vat_customer = fields.Monetary(
        string='Tiền VAT (Thu khách)',
        currency_field='currency_id',
        compute='_compute_tax_vat_customer', 
        store=True, 
        tracking=True
    )

    # Thêm trường quản lý trạng thái giá
    price_status = fields.Selection([
        ('new', 'Mới tạo'),
        ('calculated', 'Đã tính giá'),
        ('proposed', 'Đề xuất'),
        ('auto_approved', 'Đã phê duyệt tự động'),
        ('pending_approval', 'Chờ phê duyệt'),
        ('approved', 'Đã phê duyệt'),
        ('rejected', 'Đã từ chối')
    ], string='Trạng thái giá', default='new', tracking=True)

    @api.depends('dpt_price_unit', 'dpt_price_min_allowed', 'dpt_price_max_allowed')
    def _compute_can_request_price_approval(self):
        for line in self:
            is_in_range = (line.dpt_price_min_allowed <= line.dpt_price_unit <= line.dpt_price_max_allowed)
            if not line.dpt_price_unit or is_in_range:
                line.can_request_price_approval = False
            else:
                line.can_request_price_approval = True

    @api.depends('declaration_type', 'dpt_price_usd', 'dpt_price_cny_vnd', 'dpt_price_krw_vnd',
                 'dpt_exchange_rate_basic_final', 'dpt_sl1')
    def _compute_dpt_basic_value(self):
        for rec in self:
            price = 0
            if rec.declaration_type == 'usd':
                price = rec.dpt_price_usd
            elif rec.declaration_type == 'cny':
                price = rec.dpt_price_cny_vnd
            elif rec.declaration_type == 'krw':
                price = rec.dpt_price_krw_vnd

            rec.dpt_basic_value = price * (rec.dpt_exchange_rate_basic_final or 0) * rec.dpt_sl1

    @api.depends('dpt_price_krw_vnd', 'dpt_sl1', 'declaration_type')
    def _compute_dpt_total_krw_vnd(self):
        for rec in self:
            rec.dpt_total_krw_vnd = rec.dpt_price_krw_vnd * rec.currency_krw_id.rate_ids[:1].company_rate * rec.dpt_sl1

    @api.depends('declaration_type', 'dpt_price_usd', 'dpt_price_cny_vnd', 'dpt_price_krw_vnd', 'dpt_tax_other',
                 'dpt_tax_import')
    # def _compute_dpt_price_unit(self):
    #     """
    #     Logic tính giá XHĐ mong muốn từ giá khai báo:
        
    #     1. Xác định giá khai báo dựa trên loại tiền (USD, CNY, KRW)
    #     2. Lấy tỷ giá công ty tương ứng
    #     3. Công thức: dpt_price_unit = ((giá khai * 0.1) + thuế NK + thuế khác) * tỷ giá
        
    #     Lưu ý: Hệ số 0.1 là một hằng số được sử dụng trong công thức.
    #     """
    #     for rec in self:
    #         dpt_price = 0
    #         company_rate = 1
            
    #         # Xác định giá và tỷ giá theo loại tiền khai báo
    #         if rec.declaration_type == 'usd':
    #             dpt_price = rec.dpt_price_usd
    #             company_rate = rec.currency_usd_id.rate_ids[:1].company_rate
    #         elif rec.declaration_type == 'cny':
    #             dpt_price = rec.dpt_price_cny_vnd
    #             company_rate = rec.currency_cny_id.rate_ids[:1].company_rate
    #         elif rec.declaration_type == 'krw':
    #             dpt_price = rec.dpt_price_krw_vnd
    #             company_rate = rec.currency_krw_id.rate_ids[:1].company_rate
            
    #         # Áp dụng công thức tính giá XHĐ mong muốn
    #         rec.dpt_price_unit = ((dpt_price * 0.1) + rec.dpt_tax_import + rec.dpt_tax_other) * (company_rate or 1)

    # def _inverse_dpt_price_unit(self):
    #     """
    #     Logic tính ngược từ giá XHĐ mong muốn sang giá khai báo:
        
    #     1. Bắt đầu từ giá XHĐ mong muốn
    #     2. Chia cho tỷ giá để chuyển về ngoại tệ
    #     3. Trừ đi các khoản thuế NK và thuế khác
    #     4. Chia cho hệ số 0.1 để lấy giá khai báo gốc
    #     5. Cập nhật trực tiếp vào DB theo loại tiền khai báo
        
    #     Các xử lý ngoại lệ:
    #     - Kiểm tra tỷ giá > 0 để tránh chia cho 0
    #     - Kiểm tra base_calculation để tránh chia cho 0
    #     - Xử lý ngoại lệ ZeroDivisionError
    #     """
    #     for rec in self:
    #         dpt_price = 1
            
    #         # Kiểm tra và xử lý tỷ giá
    #         if rec.dpt_exchange_rate:
    #             dpt_exchange_rate = 1
    #             if rec.dpt_exchange_rate > 0:
    #                 dpt_exchange_rate = rec.dpt_exchange_rate
                    
    #             # Tính toán giá khai từ giá XHĐ mong muốn với xử lý ngoại lệ
    #             try:
    #                 if dpt_exchange_rate != 0:
    #                     # Bước 1: Chia giá XHĐ cho tỷ giá để chuyển về ngoại tệ
    #                     # Bước 2: Trừ đi thuế NK và thuế khác
    #                     base_calculation = (rec.dpt_price_unit / dpt_exchange_rate) - rec.dpt_tax_import - rec.dpt_tax_other
                        
    #                     # Bước 3: Chia cho hệ số 0.1 để lấy giá khai báo gốc
    #                     if base_calculation != 0:
    #                         dpt_price = base_calculation / 0.1
    #                     else:
    #                         dpt_price = 0  # Trường hợp base_calculation = 0
    #                 else:
    #                     dpt_price = 0  # Trường hợp tỷ giá = 0
    #             except ZeroDivisionError:
    #                 dpt_price = 0  # Xử lý ngoại lệ chia cho 0
            
    #         # Cập nhật giá khai báo theo loại tiền vào DB
    #         if rec.declaration_type == 'usd':
    #             self.env.cr.execute(
    #                 "UPDATE dpt_export_import_line SET dpt_price_usd = %s WHERE id = %s",
    #                 (dpt_price, rec.id)
    #             )
    #         elif rec.declaration_type == 'cny':
    #             self.env.cr.execute(
    #                 "UPDATE dpt_export_import_line SET dpt_price_cny_vnd = %s WHERE id = %s",
    #                 (dpt_price, rec.id)
    #             )
    #         elif rec.declaration_type == 'krw':
    #             self.env.cr.execute(
    #                 "UPDATE dpt_export_import_line SET dpt_price_krw_vnd = %s WHERE id = %s",
    #                 (dpt_price, rec.id)
    #             )

    def action_check_lot_name(self):
        if not self.stock_picking_ids:
            raise UserError(f"Chưa được cập nhật mã lô, vui lòng kiểm tra lại!!!")

    @api.onchange('declaration_type')
    def onchange_dpt_exchange_rate(self):
        for rec in self:
            company_rate = 0
            if rec.declaration_type == 'usd':
                currency_usd_id = self.env['res.currency'].search(
                    [('category', '=', 'import_export'), ('category_code', '=', 'USD')], limit=1)
                company_rate = currency_usd_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'cny':
                currency_cny_id = self.env['res.currency'].search(
                    [('category', '=', 'import_export'), ('category_code', '=', 'CNY')], limit=1)
                company_rate = currency_cny_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'krw':
                currency_krw_id = self.env['res.currency'].search(
                    [('category', '=', 'import_export'), ('category_code', '=', 'KRW')], limit=1)
                company_rate = currency_krw_id.rate_ids[:1].company_rate
            if company_rate != 0:
                rec.dpt_exchange_rate = company_rate
            else:
                rec.dpt_exchange_rate = 0
    
    @api.onchange('declaration_type')
    def onchange_dpt_exchange_rate_basic(self):
        for rec in self:
            company_rate_basic = 0
            if rec.declaration_type == 'usd':
                currency_usd_id = self.env['res.currency'].search(
                    [('category', '=', 'basic'), ('category_code', '=', 'USD')], limit=1)
                company_rate_basic = currency_usd_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'cny':
                currency_cny_id = self.env['res.currency'].search(
                    [('category', '=', 'basic'), ('category_code', '=', 'CNY')], limit=1)
                company_rate_basic = currency_cny_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'krw':
                currency_krw_id = self.env['res.currency'].search(
                    [('category', '=', 'basic'), ('category_code', '=', 'KRW')], limit=1)
                company_rate_basic = currency_krw_id.rate_ids[:1].company_rate
            if company_rate_basic != 0:
                rec.dpt_exchange_rate_basic = company_rate_basic
            else:
                rec.dpt_exchange_rate_basic = 0

    @api.depends('declaration_type')
    def _compute_dpt_exchange_rate(self):
        for rec in self:
            company_rate = 0
            if rec.declaration_type == 'usd':
                currency_usd_id = self.env['res.currency'].search(
                    [('category', '=', 'import_export'), ('category_code', '=', 'USD')], limit=1)
                company_rate = currency_usd_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'cny':
                currency_cny_id = self.env['res.currency'].search(
                    [('category', '=', 'import_export'), ('category_code', '=', 'CNY')], limit=1)
                company_rate = currency_cny_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'krw':
                currency_krw_id = self.env['res.currency'].search(
                    [('category', '=', 'import_export'), ('category_code', '=', 'KRW')], limit=1)
                company_rate = currency_krw_id.rate_ids[:1].company_rate
            if company_rate != 0:
                rec.dpt_exchange_rate = company_rate
            else:
                rec.dpt_exchange_rate = 0
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('product_id', operator, name), ('name', operator, name), ('sale_id', operator, name)]
        import_line = self.search(domain + args, limit=limit)
        return import_line.name_get()

    def _compute_picking_count(self):
        for item in self:
            picking_ids = self.env['stock.picking'].sudo().search(
                [('is_main_incoming', '=', True), ('sale_purchase_id', '=', item.sale_id.id)])
            item.picking_count = len(picking_ids)

    def action_view_main_incoming_picking(self):
        picking_ids = self.env['stock.picking'].sudo().search(
            [('is_main_incoming', '=', True), ('sale_purchase_id', '=', self.sale_id.id)])
        action = self.env.ref('stock.stock_picking_action_picking_type').sudo().read()[0]
        context = {
            'delete': False,
            'create': False,
        }
        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        action['domain'] = [('id', 'in', picking_ids.ids)]
        return action

    @api.depends('sale_id', 'sale_id.employee_cs')
    def compute_sale_user(self):
        for item in self:
            item.sale_user_id = item.sale_id.employee_cs.user_id

    def button_confirm_item_description(self):
        self.is_readonly_item_description = True
        picking_ids = self.env['stock.picking'].sudo().search([('sale_purchase_id', '=', self.sale_id.id)])
        picking_ids.exported_label = True

    @api.depends('sale_id')
    def _compute_domain_picking_package(self):
        for item in self:
            picking_ids = self.env['stock.picking'].search(
                [('sale_purchase_id', '=', item.sale_id.id), ('is_main_incoming', '=', True)])
            item.available_picking_ids = picking_ids
            item.available_package_ids = picking_ids.package_ids

    def action_confirmed(self):
        # self.action_check_lot_name()
        self.state = 'confirmed'

    def action_wait_confirm(self):
        # self.action_check_lot_name()
        self.state = 'wait_confirm'

    @api.onchange('product_history_id')
    def onchange_get_data_product_history(self):
        if self.product_history_id:
            self.dpt_english_name = self.product_history_id.dpt_english_name
            self.dpt_description = self.product_history_id.dpt_description
            self.dpt_n_w_kg = self.product_history_id.dpt_n_w_kg
            self.dpt_g_w_kg = self.product_history_id.dpt_g_w_kg
            self.dpt_uom_id = self.product_history_id.dpt_uom_id
            self.dpt_uom2_ecus_id = self.product_history_id.dpt_uom2_ecus_id
            self.dpt_price_kd = self.product_history_id.dpt_price_kd
            self.dpt_tax_import = self.product_history_id.dpt_tax_import
            self.dpt_amount_tax_import = self.product_history_id.dpt_amount_tax_import
            self.dpt_tax_ecus5 = self.product_history_id.dpt_tax_ecus5
            self.dpt_tax = self.product_history_id.dpt_tax
            self.dpt_amount_tax = self.product_history_id.dpt_amount_tax
            # self.dpt_exchange_rate = self.product_history_id.dpt_exchange_rate
            self.hs_code_id = self.product_history_id.hs_code_id
            self.dpt_sl1 = self.product_history_id.dpt_sl1
            self.dpt_uom1_id = self.product_history_id.dpt_uom1_id
            self.dpt_sl2 = self.product_history_id.dpt_sl2
            self.dpt_price_usd = self.product_history_id.dpt_price_usd
            self.dpt_price_cny_vnd = self.product_history_id.dpt_price_cny_vnd
            self.dpt_tax_other = self.product_history_id.dpt_tax_other
            self.dpt_total = self.product_history_id.dpt_total
            self.declaration_type = self.product_history_id.declaration_type

    @api.depends('dpt_description')
    def _get_name(self):
        for rec in self:
            rec.name = rec.dpt_description

    def action_unlink(self):
        self.export_import_id = None

    @api.onchange('hs_code_id')
    def get_data_vat_hs_code(self):
        self.dpt_tax = self.hs_code_id.dpt_vat / 100
        self.dpt_tax_import = self.hs_code_id.dpt_acfta / 100

    @api.depends('dpt_price_usd', 'dpt_exchange_rate', 'dpt_sl1')
    def _compute_dpt_total_usd_vnd(self):
        for rec in self:
            rec.dpt_total_usd_vnd = rec.dpt_price_usd * rec.dpt_exchange_rate * rec.dpt_sl1

    @api.depends('dpt_price_cny_vnd', 'dpt_sl1')
    def _compute_dpt_total_usd(self):
        for rec in self:
            rec.dpt_total_usd = rec.dpt_price_usd * rec.dpt_sl1

    @api.depends('dpt_price_cny_vnd', 'dpt_exchange_rate', 'dpt_sl1')
    def _compute_dpt_total_cny_vnd(self):
        for rec in self:
            rec.dpt_total_cny_vnd = rec.dpt_price_cny_vnd * rec.dpt_exchange_rate * rec.dpt_sl1

    @api.depends('dpt_tax_import', 'dpt_total_cny_vnd', 'declaration_type', 'dpt_total_usd_vnd')
    def _compute_dpt_amount_tax_import(self):
        for rec in self:
            if rec.declaration_type == 'usd':
                rec.dpt_amount_tax_import = rec.dpt_tax_import * rec.dpt_total_usd_vnd
            else:
                rec.dpt_amount_tax_import = rec.dpt_tax_import * rec.dpt_total_cny_vnd

    @api.depends('dpt_tax', 'dpt_total_cny_vnd', 'declaration_type', 'dpt_total_usd_vnd', 'dpt_amount_tax_import',
                 'dpt_amount_tax_other')
    def _compute_dpt_amount_tax(self):
        for rec in self:
            if rec.declaration_type == 'usd':
                rec.dpt_amount_tax = rec.dpt_tax * (
                        rec.dpt_total_usd_vnd + rec.dpt_amount_tax_import + rec.dpt_amount_tax_other)
            else:
                rec.dpt_amount_tax = rec.dpt_tax * (
                        rec.dpt_total_cny_vnd + rec.dpt_amount_tax_import + rec.dpt_amount_tax_other)

    @api.depends('dpt_tax_other', 'dpt_total_cny_vnd', 'declaration_type', 'dpt_total_usd_vnd')
    def _compute_dpt_amount_tax_other(self):
        for rec in self:
            if rec.declaration_type == 'usd':
                rec.dpt_amount_tax_other = rec.dpt_tax_other * rec.dpt_total_usd_vnd
            else:
                rec.dpt_amount_tax_other = rec.dpt_tax_other * rec.dpt_total_cny_vnd

    @api.model
    def create(self, vals_list):
        res = super(DptExportImportLine, self).create(vals_list)
        for rec in res:
            val_update_sale_line = {}
            val_update_sale_line.update({
                'payment_exchange_rate': rec.dpt_exchange_rate,
                'import_tax_rate': rec.dpt_tax_import,
                'vat_tax_rate': rec.dpt_tax,
                'other_tax_rate': rec.dpt_tax_other,
                'total_tax_amount': rec.dpt_total_vat,
                'hs_code_id': rec.hs_code_id,
                'import_tax_amount': rec.dpt_amount_tax_import,
                'vat_tax_amount': rec.dpt_amount_tax,
                'other_tax_amount': rec.dpt_amount_tax_other,

            })
            rec.sale_line_id.write(val_update_sale_line)
            
            # Thiết lập trạng thái giá ban đầu
            if not rec.price_status:
                rec.price_status = 'new'
            # Tính toán giá hệ thống và giá thực tế ban đầu
            rec._compute_allowed_prices()
            
        return res

    def write(self, vals):
        # Kiểm tra trước khi ghi để đảm bảo tính nhất quán
        for rec in self:
            # Xử lý khi đã phê duyệt - không cho thay đổi giá
            if rec.approval_request_id and rec.approval_request_id.request_status == 'approved':
                if 'dpt_price_unit' in vals:
                    raise UserError(_("Giá XHĐ đã được phê duyệt và không thể thay đổi"))
                
                # Ngay cả khi chi phí thay đổi cũng không thay đổi giá thực tế
                if any(field in vals for field in ['dpt_cost_of_goods', 'dpt_unit_cost', 
                                                 'dpt_allocated_cost_general', 'dpt_allocated_cost_specific']):
                    # Thông báo nhưng vẫn cho phép thay đổi chi phí
                    self.env.user.notify_warning(
                        title=_('Cảnh báo'),
                        message=_('Giá XHĐ đã được phê duyệt và sẽ không thay đổi ngay cả khi chi phí thay đổi')
                    )
            
            # Xử lý khi đang chờ phê duyệt - không cho thay đổi giá
            elif rec.approval_request_id and rec.approval_request_id.request_status == 'pending':
                if 'dpt_price_unit' in vals:
                    raise UserError(_("Không thể thay đổi giá khi đang chờ phê duyệt"))

        res = super(DptExportImportLine, self).write(vals)

        for rec in self:
            if 'stock_picking_ids' in vals and rec.stock_picking_ids:
                rec.stock_picking_ids._compute_valid_cutlist()
            
            val_update_sale_line = {}
            val_update_sale_line.update({
                'payment_exchange_rate': rec.dpt_exchange_rate,
                'import_tax_rate': rec.dpt_tax_import,
                'vat_tax_rate': rec.dpt_tax,
                'other_tax_rate': rec.dpt_tax_other,
                'total_tax_amount': rec.dpt_total_vat,
                'hs_code_id': rec.hs_code_id,
                'import_tax_amount': rec.dpt_amount_tax_import,
                'vat_tax_amount': rec.dpt_amount_tax,
                'other_tax_amount': rec.dpt_amount_tax_other,
            })
            
            if rec.sale_line_id:
                rec.sale_line_id.write(val_update_sale_line)

            if rec.sale_line_id.id:
                if 'dpt_uom1_id' in vals or 'dpt_sl1' in vals or 'dpt_price_unit' in vals:
                    update_query = """
                            UPDATE sale_order_line
                            SET product_uom = %s, product_uom_qty = %s, price_unit = %s, price_subtotal = %s
                            WHERE id = %s
                            """
                    self.env.cr.execute(update_query,
                                        (rec.dpt_uom1_id.id, rec.dpt_sl1, rec.dpt_price_unit,
                                         rec.dpt_sl1 * rec.dpt_price_unit, rec.sale_line_id.id))
            
            # === XỬ LÝ CẬP NHẬT GIÁ XHĐ THỰC TẾ ===
            
            # 1. XỬ LÝ CHI PHÍ THAY ĐỔI
            if 'dpt_cost_of_goods' in vals or 'dpt_unit_cost' in vals:
                # Nếu đã có yêu cầu phê duyệt được duyệt, không thay đổi giá thực tế
                if rec.approval_request_id and rec.approval_request_id.request_status == 'approved':
                    # Không thay đổi dpt_actual_price - giá đã được phê duyệt
                    rec.message_post(
                        body=_("Chi phí đã thay đổi nhưng giá XHĐ thực tế đã được phê duyệt nên không thay đổi.")
                    )
                # Nếu có yêu cầu phê duyệt đang chờ, hủy và quay về giá hệ thống
                elif rec.approval_request_id and rec.approval_request_id.request_status == 'pending':
                    old_request = rec.approval_request_id
                    old_request.action_cancel()
                    # Làm tròn giá thực tế lên đến chục đồng
                    rec.dpt_actual_price = self._round_up_to_ten(rec.dpt_system_price)
                    rec.price_status = 'calculated'
                    rec.price_revalidation_required = True
                    
                    # Thông báo
                    rec.message_post(
                        body=_("Chi phí đã thay đổi. Yêu cầu phê duyệt giá đã bị hủy. "
                              "Giá XHĐ thực tế đã cập nhật về giá hệ thống.")
                    )
                # Trường hợp không có phê duyệt
                else:
                    # Cập nhật giá thực tế theo giá hệ thống mới và làm tròn lên đến chục đồng
                    rec.dpt_actual_price = self._round_up_to_ten(rec.dpt_system_price)
                    rec.price_status = 'calculated'
                    rec.message_post(
                        body=_("Chi phí đã thay đổi. Giá XHĐ thực tế đã được cập nhật về giá hệ thống %s %s.") %
                        (format(rec.dpt_actual_price, '.2f'), rec.currency_id.symbol)
                    )
            
            # 2. XỬ LÝ THAY ĐỔI GIÁ XHĐ MONG MUỐN
            if 'dpt_price_unit' in vals:
                price = rec.dpt_price_unit
                
                # Bỏ qua nếu giá không hợp lệ
                if not price:
                    # Làm tròn giá thực tế lên đến chục đồng
                    rec.dpt_actual_price = self._round_up_to_ten(rec.dpt_system_price)
                    rec.price_status = 'calculated'
                    rec.message_post(
                        body=_("Giá XHĐ mong muốn không hợp lệ. Giá XHĐ thực tế đã được đặt về giá hệ thống %s %s.") %
                        (format(rec.dpt_actual_price, '.2f'), rec.currency_id.symbol)
                    )
                    continue
                    
                # Kiểm tra giá trong/ngoài khoảng
                if rec.dpt_price_min_allowed <= price <= rec.dpt_price_max_allowed:
                    # Giá trong khoảng - tự động chấp nhận và làm tròn lên đến chục đồng
                    rec.dpt_actual_price = self._round_up_to_ten(price)
                    rec.price_status = 'auto_approved'
                    rec.message_post(
                        body=_("Giá XHĐ mong muốn %s %s nằm trong khoảng cho phép và đã được tự động phê duyệt.") %
                        (format(rec.dpt_actual_price, '.2f'), rec.currency_id.symbol)
                    )
                    
                    # Hủy yêu cầu phê duyệt nếu có
                    if rec.approval_request_id and rec.approval_request_id.request_status == 'pending':
                        rec.approval_request_id.action_cancel()
                        rec.message_post(body=_("Giá đã nằm trong khoảng cho phép. Yêu cầu phê duyệt đã bị hủy."))
                else:
                    # Giá ngoài khoảng - cần phê duyệt
                    rec.dpt_actual_price = self._round_up_to_ten(rec.dpt_system_price)  # Sử dụng giá hệ thống và làm tròn
                    rec.price_status = 'proposed'  # Đánh dấu đã đề xuất
                    rec.message_post(
                        body=_("Giá XHĐ mong muốn %s %s nằm ngoài khoảng cho phép. Cần tạo yêu cầu phê duyệt.") %
                        (format(price, '.2f'), rec.currency_id.symbol)
                    )

        return res

    @api.onchange('sale_line_id')
    def onchange_sale_order_line(self):
        if self.sale_line_id:
            self.sale_id = self.sale_line_id.order_id
            self.product_id = self.sale_line_id.product_id
            self.dpt_english_name = self.sale_line_id.product_id.dpt_english_name
            self.dpt_description = self.sale_line_id.product_id.dpt_description
            self.dpt_n_w_kg = self.sale_line_id.product_id.dpt_n_w_kg
            self.dpt_g_w_kg = self.sale_line_id.product_id.dpt_g_w_kg
            self.dpt_uom_id = self.sale_line_id.product_id.dpt_uom_id
            self.dpt_price_kd = self.sale_line_id.product_id.dpt_price_kd
            self.dpt_tax_import = self.sale_line_id.import_tax_rate
            self.dpt_amount_tax_import = self.sale_line_id.import_tax_amount
            self.dpt_tax_other = self.sale_line_id.other_tax_rate
            self.dpt_amount_tax_other = self.sale_line_id.other_tax_amount
            self.dpt_tax_import = self.sale_line_id.import_tax_rate
            self.dpt_tax_ecus5 = self.sale_line_id.product_id.dpt_tax_ecus5
            self.dpt_tax = self.sale_line_id.vat_tax_rate
            self.dpt_amount_tax = self.sale_line_id.dpt_amount_tax
            # self.dpt_exchange_rate = self.sale_line_id.payment_exchange_rate
            self.dpt_uom1_id = self.sale_line_id.product_uom
            self.dpt_sl1 = self.sale_line_id.product_uom_qty
            self.dpt_sl2 = self.sale_line_id.dpt_sl2

    @api.depends('dpt_amount_tax_import', 'dpt_amount_tax', 'dpt_amount_tax_other')
    def _compute_total_vat(self):
        for rec in self:
            rec.dpt_total_vat = rec.dpt_amount_tax_import + rec.dpt_amount_tax + rec.dpt_amount_tax_other

    def restore_information_to_product(self):
        self.product_id.dpt_english_name = self.dpt_english_name
        self.product_id.dpt_description = self.dpt_description
        self.product_id.dpt_n_w_kg = self.dpt_n_w_kg
        self.product_id.dpt_g_w_kg = self.dpt_g_w_kg
        self.product_id.dpt_uom_id = self.dpt_uom_id
        self.product_id.dpt_uom2_ecus_id = self.dpt_uom2_ecus_id
        self.product_id.dpt_uom2_id = self.dpt_uom2_id
        self.product_id.dpt_price_kd = self.dpt_price_kd
        self.product_id.dpt_price_usd = self.dpt_price_usd
        self.product_id.dpt_tax_import = self.dpt_tax_import
        self.product_id.dpt_tax_ecus5 = self.dpt_tax_ecus5
        self.product_id.dpt_tax = self.dpt_tax
        # self.product_id.dpt_exchange_rate = self.dpt_exchange_rate
        self.product_id.hs_code_id = self.hs_code_id
        self.product_id.dpt_uom1_id = self.dpt_uom1_id
        self.product_id.dpt_sl1 = self.dpt_sl1
        self.product_id.dpt_sl2 = self.dpt_sl2

    def action_update_eligible(self):
        # self.action_check_lot_name()
        self.state = 'eligible'

    @api.onchange('sale_line_id')
    def onchange_sale_line_id(self):
        self.product_id = self.sale_line_id.product_id

    @api.onchange('product_id')
    def onchange_information_product(self):
        if self.product_id:
            if self.product_id.dpt_export_import_line_ids:
                self.product_history_id = self.product_id.dpt_export_import_line_ids[0]
            else:
                self.product_history_id = None
                self.dpt_english_name = self.product_id.dpt_english_name
                self.dpt_description = self.product_id.dpt_description
                self.dpt_n_w_kg = self.product_id.dpt_n_w_kg
                self.dpt_g_w_kg = self.product_id.dpt_g_w_kg
                self.dpt_uom_id = self.product_id.dpt_uom_id
                self.dpt_uom2_ecus_id = self.product_id.dpt_uom2_ecus_id
                self.dpt_uom2_id = self.product_id.dpt_uom2_id
                self.dpt_price_kd = self.product_id.dpt_price_kd
                self.dpt_price_usd = self.product_id.dpt_price_usd
                self.dpt_tax_import = self.product_id.dpt_tax_import
                self.dpt_tax_ecus5 = self.product_id.dpt_tax_ecus5
                self.dpt_tax = self.product_id.dpt_tax
                # self.dpt_exchange_rate = self.product_id.dpt_exchange_rate
                self.dpt_uom1_id = self.product_id.dpt_uom1_id
                self.dpt_sl1 = self.product_id.dpt_sl1
                self.dpt_sl2 = self.product_id.dpt_sl2

    # dunghq
    @api.depends('product_id', 'dpt_description', 'declaration_type',
                 'brand_id', 'model_id', 'partner_id')
    def _compute_risk_reason(self):
        for record in self:
            reason = False

            # Kiểm tra các điều kiện cơ bản
            if not (record.product_id and record.dpt_description and record.id):
                record.risk_reason = reason
                continue

            # Xác định trường giá cần so sánh dựa trên declaration_type
            price_value = record.dpt_price_usd if record.declaration_type == 'usd' else record.dpt_price_cny_vnd

            # 1. Kiểm tra "Sản phẩm cũ, dòng tờ khai cũ có giá mới"
            other_lines = self.env['dpt.export.import.line'].search([
                ('product_id', '=', record.product_id.id),
                ('dpt_description', '=', record.dpt_description),
                ('id', '!=', record.id),
                ('declaration_type', '=', record.declaration_type),
                ('state', '=', 'eligible'),
            ])

            for line in other_lines:
                other_price = line.dpt_price_usd if record.declaration_type == 'usd' else line.dpt_price_cny_vnd
                if price_value != other_price:
                    reason = 'different_price'
                    break

            # 2. Kiểm tra "Hàng cùng model và nhãn hiệu khác giá khai"
            if not reason and record.brand_id and record.model_id:
                other_lines = self.env['dpt.export.import.line'].search([
                    ('brand_id', '=', record.brand_id.id),
                    ('model_id', '=', record.model_id.id),
                    ('id', '!=', record.id),
                    ('declaration_type', '=', record.declaration_type),
                    ('state', '=', 'eligible'),
                ])

                for line in other_lines:
                    other_price = line.dpt_price_usd if record.declaration_type == 'usd' else line.dpt_price_cny_vnd
                    if price_value != other_price:
                        reason = 'same_model_different_price'
                        break

            # 3. Kiểm tra "Khách hàng có đơn hàng không lấy hóa đơn"
            if not reason and record.partner_id:
                # Tìm stage "Không lấy hoá đơn" trong helpdesk
                stage_no_invoice = self.env['helpdesk.stage'].search([('name', '=', 'Không lấy hoá đơn')], limit=1)

                if stage_no_invoice:
                    # Tìm ticket có khách hàng này và ở stage "Không lấy hoá đơn"
                    risky_tickets = self.env['helpdesk.ticket'].search([
                        ('partner_id', '=', record.partner_id.id),
                        ('stage_id', '=', stage_no_invoice.id)
                    ], limit=1)

                    if risky_tickets:
                        reason = 'no_invoice'

            record.risk_reason = reason
    # dunghq

    @api.depends('dpt_basic_value', 'dpt_tax_import', 'dpt_tax_other', 'dpt_tax')
    def _compute_basic_taxes(self):
        for rec in self:
            # Tiền thuế NK = Giá trị cơ bản × Thuế NK %
            amount_tax_import_basic = rec.dpt_basic_value * rec.dpt_tax_import

            # Tiền thuế Khác XHĐ= Giá trị cơ bản × Thuế Khác%
            amount_tax_other_basic = rec.dpt_basic_value * rec.dpt_tax_other

            # Tiền thuế VAT XHĐ = (Giá trị cơ bản + Tiền thuế NK + thuế khác) × VAT %
            base_for_vat = rec.dpt_basic_value + amount_tax_import_basic + amount_tax_other_basic
            amount_tax_vat_basic = base_for_vat * rec.dpt_tax

            # Tổng thuế XHĐ = Tiền thuế NK + Tiền thuế khác + Tiền VAT
            total_tax_basic = amount_tax_import_basic + amount_tax_other_basic + amount_tax_vat_basic

            rec.dpt_amount_tax_import_basic = amount_tax_import_basic
            rec.dpt_amount_tax_other_basic = amount_tax_other_basic
            rec.dpt_amount_tax_vat_basic = amount_tax_vat_basic
            rec.dpt_total_tax_basic = total_tax_basic

    @api.depends('dpt_allocated_cost_general', 'dpt_allocated_cost_specific')
    def _compute_total_allocated_cost(self):
        for rec in self:
            rec.dpt_total_allocated_cost = rec.dpt_allocated_cost_general + rec.dpt_allocated_cost_specific

    @api.depends('dpt_basic_value', 'dpt_amount_tax_import_basic', 'dpt_amount_tax_other_basic')
    def _compute_cost_of_goods(self):
        for rec in self:
            # Sửa: Chỉ tính giá trị cơ bản + thuế NK + thuế Khác + chi phí phân bổ (không bao gồm VAT)
            rec.dpt_cost_of_goods = rec.dpt_basic_value + rec.dpt_amount_tax_import_basic + rec.dpt_amount_tax_other_basic + rec.dpt_total_allocated_cost

    @api.depends('dpt_cost_of_goods', 'dpt_sl1')
    def _compute_unit_cost(self):
        for rec in self:
            if rec.dpt_sl1 and rec.dpt_sl1 != 0:
                rec.dpt_unit_cost = rec.dpt_cost_of_goods / rec.dpt_sl1
            else:
                rec.dpt_unit_cost = 0.0

    @api.depends('dpt_unit_cost')
    def _compute_allowed_prices(self):
        """Tính toán khoảng giá cho phép dựa trên giá vốn và tỷ lệ lợi nhuận"""
        for rec in self:
            company = self.env.company
            min_margin = company.dpt_min_profit_margin or 1.01
            max_margin = company.dpt_max_profit_margin or 1.03

            if rec.dpt_unit_cost > 0:
                rec.dpt_price_min_allowed = rec.dpt_unit_cost * min_margin
                rec.dpt_price_max_allowed = rec.dpt_unit_cost * max_margin
                rec.dpt_system_price = rec.dpt_price_min_allowed
                
                # Gán giá trị ban đầu cho dpt_actual_price nếu chưa có
                # và chưa có yêu cầu phê duyệt được chấp nhận
                if not rec.dpt_actual_price or rec.price_status in ['new', 'calculated']:
                    if not rec.approval_request_id or rec.approval_request_id.request_status != 'approved':
                        # Làm tròn giá thực tế lên đến chục đồng
                        rec.dpt_actual_price = self._round_up_to_ten(rec.dpt_system_price)
            else:
                rec.dpt_price_min_allowed = 0
                rec.dpt_price_max_allowed = 0
                rec.dpt_system_price = 0
                if not rec.dpt_actual_price:
                    rec.dpt_actual_price = 0
                    
    @api.onchange('dpt_exchange_rate_basic')
    def onchange_dpt_exchange_rate_basic_final(self):
        for rec in self:
            rec.dpt_exchange_rate_basic_final = rec.dpt_exchange_rate_basic

    @api.onchange('dpt_price_unit')
    def _onchange_price_unit(self):
        """Kiểm tra giá và hiển thị cảnh báo"""
        for rec in self:
            # Bỏ qua khi giá trống hoặc bằng 0
            if not rec.dpt_price_unit:
                rec.price_outside_range = False
                continue
            
            # Kiểm tra nếu giá không phải số chẵn chục
            if rec.dpt_price_unit % 10 != 0:
                return {
                    'warning': {
                        'title': _('Cảnh báo về giá xuất hóa đơn'),
                        'message': _('Giá xuất hóa đơn mong muốn phải là số chẵn chục đồng! Vui lòng điều chỉnh.')
                    }
                }
                
            # Kiểm tra nếu giá nằm ngoài khoảng cho phép
            if rec.dpt_price_unit < rec.dpt_price_min_allowed or rec.dpt_price_unit > rec.dpt_price_max_allowed:
                # Đánh dấu là giá nằm ngoài khoảng cho phép
                rec.price_outside_range = True
                rec.price_temp = rec.dpt_price_unit
                
                # Hiển thị thông báo cảnh báo
                return {
                    'warning': {
                        'title': _('Giá nằm ngoài khoảng cho phép'),
                        'message': _(
                            'Giá XHĐ mong muốn ({:,.2f} {}) nằm ngoài khoảng giá cho phép: {:,.2f} - {:,.2f} {}.\n\n'
                            'Hãy sử dụng nút "Xác nhận phê duyệt" để xem các lựa chọn phê duyệt hoặc đặt lại giá.'
                        ).format(
                            rec.dpt_price_unit, rec.currency_id.symbol,
                            rec.dpt_price_min_allowed, rec.dpt_price_max_allowed, rec.currency_id.symbol
                        )
                    }
                }
            else:
                rec.price_outside_range = False
    
    def action_open_price_approval_wizard(self):
        """Mở wizard xác nhận phê duyệt giá"""
        self.ensure_one()
        
        # Nếu đã có yêu cầu phê duyệt đã được chấp nhận, hiển thị thông báo
        if self.approval_request_id and self.approval_request_id.request_status == 'approved':
            raise UserError(_("Giá XHĐ đã được phê duyệt và không thể thay đổi."))
        
        # Nếu đang có yêu cầu đang chờ, mở yêu cầu đó
        if self.approval_request_id and self.approval_request_id.request_status == 'pending':
            return {
                'name': _('Yêu cầu phê duyệt giá'),
                'type': 'ir.actions.act_window',
                'res_model': 'approval.request',
                'res_id': self.approval_request_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Thiết lập wizard với giá trị đầu vào
        return {
            'name': _('Giá nằm ngoài khoảng cho phép'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.price.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_export_import_line_id': self.id,
                'default_current_price': self.dpt_price_unit,
                'default_min_price': self.dpt_price_min_allowed,
                'default_max_price': self.dpt_price_max_allowed,
                'default_system_price': self.dpt_system_price,
                'default_currency_id': self.currency_id.id,
            }
        }

    def _create_price_approval_request(self):
        """Tạo yêu cầu phê duyệt giá"""
        self.ensure_one()
        
        # Kiểm tra xem có thể tạo phiếu phê duyệt mới không
        if self.approval_request_id:
            # Chỉ cho phép tạo mới nếu phiếu cũ đã bị từ chối hoặc hủy
            if self.approval_request_id.request_status not in ['refused', 'cancel']:
                raise UserError(_("Đã có yêu cầu phê duyệt đang hoạt động. Không thể tạo thêm yêu cầu mới."))
        
        approval_category = self.env.ref('dpt_export_import.approval_category_dpt_price_approval')
        
        if not approval_category:
            raise UserError(_("Chưa cấu hình loại phê duyệt 'Phê duyệt giá xuất hoá đơn'"))
        
        # Nếu đã có yêu cầu phê duyệt cũ, hủy nó
        if self.approval_request_id and self.approval_request_id.request_status == 'pending':
            self.approval_request_id.action_cancel()
        
        # Nếu giá bằng 0, không tạo yêu cầu phê duyệt
        if not self.dpt_price_unit:
            return False
        
        # Tạo yêu cầu phê duyệt mới
        request_vals = {
            'name': _('Phê duyệt giá cho %s') % self.name,
            'category_id': approval_category.id,
            'request_owner_id': self.env.user.id,
            'reference': _('Dòng tờ khai: %s - Sản phẩm: %s') % (self.name, self.product_id.name),
            'date': fields.Date.today(),
            'export_import_line_id': self.id,
            'quantity': self.dpt_sl1,
            'amount': self.dpt_price_unit,
            'company_id': self.env.company.id,
        }
        
        approval_request = self.env['approval.request'].create(request_vals)
        
        # Cập nhật trạng thái thành pending sau khi tạo
        approval_request.sudo().write({'request_status': 'pending'})
        
        self.write({
            'approval_request_id': approval_request.id,
            'price_status': 'pending_approval'  # Cập nhật trạng thái giá
        })
        
        # Thêm thông báo
        self.message_post(body=_("Đã tạo yêu cầu phê duyệt giá %s.") % approval_request.name)
        
        return approval_request

    @api.onchange('approval_status')
    def _onchange_approval_status(self):
        """Xử lý khi trạng thái phê duyệt thay đổi"""
        for rec in self:
            if rec.approval_status == 'approved':
                rec.action_approve_price()
            elif rec.approval_status == 'refused':
                rec.action_reject_price()

    def action_approve_price(self):
        """Xử lý sau khi phê duyệt - Cập nhật giá thực tế và xóa cờ cảnh báo"""
        self.ensure_one()
        # Làm tròn giá mong muốn lên đến chục đồng trước khi phê duyệt
        rounded_price = self._round_up_to_ten(self.dpt_price_unit)
        self.write({
            'dpt_actual_price': rounded_price,
            'price_revalidation_required': False,
            'price_status': 'approved'  # Chỉ dùng trạng thái "đã phê duyệt"
        })
        
        # Thêm thông báo
        self.message_post(body=_("Giá XHĐ %s %s đã được phê duyệt và không thể thay đổi.") % 
                        (format(rounded_price, '.2f'), self.currency_id.symbol))

    def action_reject_price(self):
        """Xử lý khi phê duyệt bị từ chối"""
        self.ensure_one()
        # Làm tròn giá hệ thống lên đến chục đồng
        rounded_system_price = self._round_up_to_ten(self.dpt_system_price)
        self.write({
            'dpt_actual_price': rounded_system_price,
            'price_status': 'rejected'
        })
        
        # Thêm thông báo
        self.message_post(body=_("Yêu cầu phê duyệt giá đã bị từ chối. Giá XHĐ thực tế là %s %s.") %
                        (format(rounded_system_price, '.2f'), self.currency_id.symbol))

    @api.depends('declaration_type', 'dpt_price_usd', 'dpt_price_cny_vnd', 'dpt_price_krw_vnd',
             'dpt_exchange_rate', 'dpt_amount_tax_import', 'dpt_amount_tax_other', 'dpt_tax', 'dpt_sl1')
    def _compute_tax_vat_customs(self):
        for rec in self:
            # Xác định giá khai báo dựa trên loại tiền
            price = 0
            if rec.declaration_type == 'usd':
                price = rec.dpt_price_usd
            elif rec.declaration_type == 'cny':
                price = rec.dpt_price_cny_vnd
            elif rec.declaration_type == 'krw':
                price = rec.dpt_price_krw_vnd
            
            # Tiền thuế VAT (HQ) = (Giá khai * Tỉ giá HQ * Số lượng + Tiền thuế NK + Tiền thuế Khác) * VAT(%)
            price_vnd = price * rec.dpt_exchange_rate * rec.dpt_sl1
            base_amount = price_vnd + rec.dpt_amount_tax_import + rec.dpt_amount_tax_other
            rec.dpt_amount_tax_vat_customs = base_amount * rec.dpt_tax

    @api.depends('dpt_actual_price', 'dpt_sl1', 'dpt_tax')
    def _compute_tax_vat_customer(self):
        for rec in self:
            # Tiền VAT (Thu khách) = Giá XHĐ thực tế * số lượng 1 * VAT(%)
            rec.dpt_amount_tax_vat_customer = rec.dpt_actual_price * rec.dpt_sl1 * rec.dpt_tax

    @api.constrains('dpt_price_unit', 'approval_request_id', 'price_status')
    def _check_price_constraints(self):
        """Kiểm tra các ràng buộc về giá"""
        for rec in self:
            # Nếu đã có yêu cầu phê duyệt được duyệt, phải ở trạng thái approved
            if rec.approval_request_id and rec.approval_request_id.request_status == 'approved':
                if rec.price_status != 'approved':
                    raise ValidationError(_("Giá XHĐ đã được phê duyệt nhưng trạng thái không phù hợp. Vui lòng liên hệ quản trị viên."))

    @api.depends('approval_status')
    def _compute_approval_status_change(self):
        """Theo dõi thay đổi trạng thái phê duyệt"""
        for rec in self:
            # Field này chỉ là để đảm bảo computed field hoạt động
            # Việc xử lý trạng thái đã được thực hiện trong ApprovalRequest.write()
            pass

    @api.constrains('dpt_price_unit')
    def _check_price_unit_multiple_of_ten(self):
        """Kiểm tra giá xuất hóa đơn mong muốn phải là số chẵn chục"""
        for rec in self:
            if rec.dpt_price_unit and rec.dpt_price_unit % 10 != 0:
                raise ValidationError(_("Giá xuất hóa đơn mong muốn phải là số chẵn chục đồng!"))

    # Sửa phương thức làm tròn để làm tròn lên đến chục đồng gần nhất
    def _round_up_to_ten(self, value):
        """Làm tròn giá trị lên đến chục đồng gần nhất
        Ví dụ: 20091 -> 20100, 20011 -> 20020, 284672 -> 284680
        """
        if not value:
            return 0
        # Làm tròn lên đến chục đồng gần nhất
        remainder = value % 10
        if remainder > 0:
            return value + (10 - remainder)
        return value

