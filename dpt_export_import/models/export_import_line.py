# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
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
    dpt_exchange_rate = fields.Float(string='Tỉ giá XNK', tracking=True, currency_field='currency_id', store=True,
                                     digits=(12, 4), compute="compute_dpt_exchange_rate")
    hs_code_id = fields.Many2one('dpt.export.import.acfta', string='HS Code', tracking=True)
    dpt_code_hs = fields.Char(string='H')
    dpt_sl1 = fields.Float(string='SL1', tracking=True, digits=(12, 4))
    dpt_price_unit = fields.Monetary(string='Đơn giá xuất hoá đơn', tracking=True, currency_field='currency_id',
                                     compute="_compute_dpt_price_unit", inverse="_inverse_dpt_price_unit", store=True)
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

    @api.depends('dpt_price_krw_vnd', 'dpt_sl1', 'declaration_type')
    def _compute_dpt_total_krw_vnd(self):
        for rec in self:
            rec.dpt_total_krw_vnd = rec.dpt_price_krw_vnd * rec.currency_krw_id.rate_ids[:1].company_rate * rec.dpt_sl1

    # @api.onchange('declaration_type', 'dpt_price_unit', 'dpt_tax_other', 'dpt_tax_import')
    # def onchange_dpt_price(self):
    #     for rec in self:
    #         company_rate = 1
    #
    #         if rec.declaration_type == 'usd':
    #             company_rate = rec.currency_usd_id.rate_ids[:1].company_rate or 1
    #         elif rec.declaration_type == 'cny':
    #             company_rate = rec.currency_cny_id.rate_ids[:1].company_rate or 1
    #         elif rec.declaration_type == 'krw':
    #             company_rate = rec.currency_krw_id.rate_ids[:1].company_rate or 1
    #         else:
    #             continue  # Nếu không có declaration_type hợp lệ, bỏ qua
    #         # Đảm bảo company_rate không bị 0
    #         company_rate = 1 / company_rate if company_rate else 1
    #         # Tính giá trị chia
    #         divisor = 0.1 * (1 + (rec.dpt_tax_import or 0) + (rec.dpt_tax_other or 0))
    #         dpt_price = (rec.dpt_price_unit * company_rate) / divisor if divisor else 0
    #         # Gán giá trị vào đúng trường
    #         if rec.declaration_type == 'usd':
    #             rec.dpt_price_usd = dpt_price
    #         elif rec.declaration_type == 'cny':
    #             rec.dpt_price_cny_vnd = dpt_price
    #         elif rec.declaration_type == 'krw':
    #             rec.dpt_price_krw_vnd = dpt_price
    #
    # @api.onchange('declaration_type', 'dpt_price_usd', 'dpt_price_cny_vnd', 'dpt_price_krw_vnd', 'dpt_tax_other',
    #               'dpt_tax_import')
    # def onchange_dpt_price_unit(self):
    #     for rec in self:
    #         dpt_price = 0
    #         company_rate = 1
    #         if rec.declaration_type == 'usd':
    #             dpt_price = rec.dpt_price_usd
    #             company_rate = rec.currency_usd_id.rate_ids[:1].company_rate
    #         elif rec.declaration_type == 'cny':
    #             dpt_price = rec.dpt_price_cny_vnd
    #             company_rate = rec.currency_cny_id.rate_ids[:1].company_rate
    #         elif rec.declaration_type == 'krw':
    #             dpt_price = rec.dpt_price_krw_vnd
    #             company_rate = rec.currency_krw_id.rate_ids[:1].company_rate
    #         rec.dpt_price_unit = (dpt_price * 0.1) * (1 + rec.dpt_tax_import + rec.dpt_tax_other) * (1 / company_rate)

    @api.depends('declaration_type', 'dpt_price_usd', 'dpt_price_cny_vnd', 'dpt_price_krw_vnd', 'dpt_tax_other',
                 'dpt_tax_import')
    def _compute_dpt_price_unit(self):
        for rec in self:
            dpt_price = 0
            company_rate = 1
            if rec.declaration_type == 'usd':
                dpt_price = rec.dpt_price_usd
                company_rate = rec.currency_usd_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'cny':
                dpt_price = rec.dpt_price_cny_vnd
                company_rate = rec.currency_cny_id.rate_ids[:1].company_rate
            elif rec.declaration_type == 'krw':
                dpt_price = rec.dpt_price_krw_vnd
                company_rate = rec.currency_krw_id.rate_ids[:1].company_rate
            rec.dpt_price_unit = ((dpt_price * 0.1) + rec.dpt_tax_import + rec.dpt_tax_other) * (company_rate or 1)

    def _inverse_dpt_price_unit(self):
        for rec in self:
            dpt_price = ((rec.dpt_price_unit / rec.dpt_exchange_rate) - rec.dpt_tax_import - rec.dpt_tax_other) / 0.1
            if rec.declaration_type == 'usd':
                query = f"""
                        UPDATE dpt_export_import_line
                        SET dpt_price_usd = %s
                        WHERE id = %s
                    """
                self.env.cr.execute(query, (dpt_price, rec.id))
            elif rec.declaration_type == 'cny':
                query = f"""
                                        UPDATE dpt_export_import_line
                                        SET dpt_price_cny_vnd = %s
                                        WHERE id = %s
                                    """
                self.env.cr.execute(query, (dpt_price, rec.id))
            elif rec.declaration_type == 'krw':
                query = f"""
                                        UPDATE dpt_export_import_line
                                        SET dpt_price_krw_vnd = %s
                                        WHERE id = %s
                                    """
                self.env.cr.execute(query, (dpt_price, rec.id))

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

    @api.depends('declaration_type')
    def compute_dpt_exchange_rate(self):
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
        for rec in self:
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
        return res

    def write(self, vals):
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
            rec.sale_line_id.write(val_update_sale_line)
            if 'dpt_price_unit' in vals and 'dpt_price_usd' not in vals and 'dpt_price_krw_vnd' not in vals and 'dpt_price_cny_vnd' not in vals:
                self._inverse_dpt_price_unit()
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
        return res

    # def write(self, vals):
    #     res = super(SaleOrderLine, self).write(vals)
    #     if 'product_uom' in vals or 'product_uom_qty' in vals:
    #         for dpt_export_import_line_id in self.dpt_export_import_line_ids:
    #             dpt_export_import_line_id.dpt_uom1_id = self.product_uom
    #             dpt_export_import_line_id.dpt_sl1 = self.product_uom_qty
    #     return res

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
