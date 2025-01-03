# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
_logger = logging.getLogger(__name__)
class DptExportImportGate(models.Model):
    _name = "dpt.export.import.gate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import Gate'

    name = fields.Char(string='Name')


class DptExportImport(models.Model):
    _name = "dpt.export.import"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import'

    name = fields.Char(string='Title', tracking=True)
    code = fields.Char(string='Code', tracking=True)
    invoice_code = fields.Char(string='Invoice Code', tracking=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sale_ids = fields.Many2many('sale.order', string='Select Sale Order', tracking=True)
    partner_importer_id = fields.Many2one('res.partner', string='Partner Importer')
    partner_exporter_id = fields.Many2one('res.partner', string='Partner Exporter')
    gate_id = fields.Many2one('dpt.export.import.gate', string='Gate Importer')
    user_id = fields.Many2one('res.users', string='User Export/Import', default=lambda self: self.env.user, tracking=True)
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    consultation_date = fields.Date(string='Consultation date')
    line_ids = fields.One2many('dpt.export.import.line', 'export_import_id', string='Export/Import Line')
    select_line_ids = fields.Many2many('dpt.export.import.line', string='Export/Import Line',
                                       domain=[('export_import_id', '=', False), ('state', '!=', 'draft')])
    dpt_tax_ecus5 = fields.Char(string='VAT ECUS5', tracking=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('draft_declaration', 'Tờ khai nháp'),
        ('confirm', 'Xác nhận tờ khai'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft', tracking=True)
    declaration_flow = fields.Selection([
        ('red', 'Red'),
        ('yellow', 'Yellow'),
        ('green', 'Green')
    ], string='Declaration Flow', default='red', tracking=True)
    dpt_n_w_kg = fields.Integer(string='Total N.W (KG)', compute="_compute_total_sum_line")
    dpt_g_w_kg = fields.Integer(string='Total G.W (KG)', compute="_compute_total_sum_line")
    total_cubic_meters = fields.Float(string='Total cubic meters', compute="_compute_total_cubic_meters")
    total_package = fields.Char(string='Total package', compute="_compute_total_package_line")
    dpt_amount_tax_import = fields.Monetary(string='Total Amount import', compute="_compute_total_sum_line",
                                            currency_field='currency_id')
    dpt_amount_tax = fields.Monetary(string='Total Amount VAT', compute="_compute_total_sum_line",
                                     currency_field='currency_id')
    dpt_amount_tax_other = fields.Monetary(string='Total Amount Tax Other', currency_field='currency_id',
                                           compute="_compute_total_sum_line")
    dpt_total_line = fields.Integer(string='Total line', compute="_compute_total_count_line")
    dpt_total_line_new = fields.Integer(string='Total line New', compute="_compute_total_count_line")
    estimated_total_amount = fields.Monetary(string='Estimated total amount', compute="_compute_estimated_total_amount",
                                             currency_field='currency_id')
    actual_total_amount = fields.Monetary(string='Actual total amount', currency_field='currency_id')
    payment_exchange_rate = fields.Float(string='Rate ECUSS', digits=(12, 4))
    shipping_slip = fields.Char(string='Shipping Slip', tracking=True)
    type_of_vehicle = fields.Char(string='Type of vehicle', tracking=True)
    driver_name = fields.Char(string='Driver Name', tracking=True)
    driver_phone_number = fields.Char(string='Driver Phone Number', tracking=True)
    vehicle_license_plate = fields.Char(string='Vehicle License Plate', tracking=True)
    declaration_type = fields.Selection([
        ('usd', 'USD'),
        ('cny', 'CNY')
    ], string='Declaration type', default='usd', tracking=True)

    @api.depends('sale_ids', 'sale_ids.volume')
    def _compute_total_cubic_meters(self):
        for rec in self:
            total_cubic_meters = 0
            for sale_id in rec.sale_ids:
                total_cubic_meters += sale_id.volume
            rec.total_cubic_meters = total_cubic_meters

    @api.onchange('declaration_type')
    def onchange_update_value_declaration_type(self):
        if self.declaration_type == 'usd':
            exchange_rate = self.env['res.currency'].search([('name', '=', 'USD')])
            self.payment_exchange_rate = exchange_rate.rate
        if self.declaration_type == 'cny':
            exchange_rate = self.env['res.currency'].search([('name', '=', 'CNY')])
            self.payment_exchange_rate = exchange_rate.rate

    @api.onchange('payment_exchange_rate')
    def onchange_update_line_payment_exchange_rate(self):
        for line_id in self.line_ids:
            line_id.dpt_exchange_rate = self.payment_exchange_rate

    @api.onchange('dpt_tax_ecus5')
    def update_dpt_tax_ecus5(self):
        for line_id in self.line_ids:
            line_id.dpt_tax_ecus5 = self.dpt_tax_ecus5

    def write(self, vals):
        old_sale_ids = self.sale_ids
        res = super(DptExportImport, self).write(vals)
        new_sale_ids = self.sale_ids
        sale_ids = old_sale_ids - new_sale_ids
        _logger.info("Removed Sale IDs: %s", sale_ids)
        for sale_id in sale_ids:
            for dpt_export_import_line_id in sale_id.dpt_export_import_line_ids:
                dpt_export_import_line_id.export_import_id = None
        return res

    @api.onchange('sale_ids')
    def onchange_add_declaration_line(self):
        for order_line_id in self.sale_ids:
            if order_line_id.dpt_export_import_line_ids:
                for dpt_export_import_line_id in order_line_id.dpt_export_import_line_ids:
                    if not dpt_export_import_line_id.export_import_id:
                        dpt_export_import_line_id.export_import_id = self.id

    def action_open_declaration_line(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_tree').id
        view_form_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.export.import.line',
            'name': _('Declaration Line'),
            'view_mode': 'tree,form',
            'domain': [('export_import_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }

    @api.depends('dpt_amount_tax_import', 'dpt_amount_tax', 'dpt_amount_tax_other')
    def _compute_estimated_total_amount(self):
        for rec in self:
            rec.estimated_total_amount = rec.dpt_amount_tax + rec.dpt_amount_tax_import + rec.dpt_amount_tax_other

    @api.depends('line_ids', 'line_ids.dpt_is_new')
    def _compute_total_count_line(self):
        for rec in self:
            rec.dpt_total_line = len(rec.line_ids)
            rec.dpt_total_line_new = len(rec.line_ids.filtered(lambda rec: rec.dpt_is_new == True))

    @api.depends('line_ids', 'line_ids.dpt_n_w_kg', 'line_ids.dpt_g_w_kg', 'line_ids.dpt_amount_tax_import',
                 'line_ids.dpt_amount_tax')
    def _compute_total_sum_line(self):
        for rec in self:
            rec.dpt_n_w_kg = sum(line.dpt_n_w_kg for line in rec.line_ids)
            rec.dpt_g_w_kg = sum(line.dpt_g_w_kg for line in rec.line_ids)
            rec.dpt_amount_tax_import = sum(line.dpt_amount_tax_import for line in rec.line_ids)
            rec.dpt_amount_tax_other = sum(line.dpt_amount_tax_other for line in rec.line_ids)
            rec.dpt_amount_tax = sum(line.dpt_amount_tax for line in rec.line_ids)

    def _compute_total_package_line(self):
        for rec in self:
            package_ids = []
            for line_id in rec.line_ids:
                for package_id in line_id.package_ids:
                    package_ids.append(package_id.id)
            if package_ids:
                query = """
                    SELECT string_agg(quantity || ' ' || name, ' + ') AS total_package 
                    FROM (
                        SELECT SUM(quantity) as  quantity, b.name ->>'en_US' as name
                        FROM purchase_order_line_package a 
                        JOIN uom_uom b on a.uom_id = b.id
                        WHERE a.id in %s 
                    GROUP BY b.name) as a
                """
                self.env.cr.execute(query, [tuple(package_ids)])
                result = self.env.cr.dictfetchone()
                rec.total_package = result.get('total_package') or ''
            else:
                rec.total_package = ''

    def action_draft_declaration(self):
        self.state = 'draft_declaration'
        for line_id in self.line_ids:
            line_id.state = 'draft_declaration'

    def action_declared(self):
        self.state = 'declared'
        for line_id in self.line_ids:
            line_id.state = 'declared'

    def action_released(self):
        self.state = 'released'
        for line_id in self.line_ids:
            line_id.state = 'released'

    def action_consulted(self):
        self.state = 'consulted'
        for line_id in self.line_ids:
            line_id.state = 'consulted'

    def action_post_control(self):
        self.state = 'post_control'
        for line_id in self.line_ids:
            line_id.state = 'post_control'

    def action_cancelled(self):
        self.state = 'cancelled'
        for line_id in self.line_ids:
            line_id.state = 'cancelled'

    def action_select_import_line(self):
        view_form_id = self.env.ref('dpt_export_import.dpt_export_import_select_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select Line'),
            'view_mode': 'form',
            'res_model': 'dpt.export.import',
            'target': 'new',
            'res_id': self.id,
            'views': [[view_form_id, 'form']],
        }

    def action_update_import_line(self):
        if self.select_line_ids:
            for select_line_id in self.select_line_ids:
                select_line_id.export_import_id = self.id


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
    dpt_exchange_rate = fields.Float(string='Exchange rate', tracking=True, currency_field='currency_id',
                                     digits=(12, 4))
    hs_code_id = fields.Many2one('dpt.export.import.acfta', string='HS Code', tracking=True)
    dpt_code_hs = fields.Char(string='H')
    dpt_sl1 = fields.Float(string='SL1', tracking=True, digits=(12, 4))
    dpt_price_unit = fields.Monetary(string='Đơn giá xuất hoá đơn', tracking=True, currency_field='currency_id')
    dpt_uom1_id = fields.Many2one('uom.uom', string='ĐVT 1', tracking=True)
    dpt_sl2 = fields.Float(string='SL2', tracking=True, digits=(12, 4))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    currency_usd_id = fields.Many2one('res.currency', string='Currency USD', default=1)
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
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
    dpt_tax_other = fields.Float(string='Tax Other (%)', tracking=True)
    dpt_amount_tax_other = fields.Monetary(string='Amount Tax Other', currency_field='currency_id',
                                           compute="_compute_dpt_amount_tax_other")
    dpt_total_vat = fields.Monetary(string='Total VAT', tracking=True, compute="_compute_total_vat",
                                    currency_field='currency_id')
    dpt_total = fields.Monetary(string='Total', tracking=True, currency_field='currency_id')
    dpt_is_new = fields.Boolean(string='Is new', tracking=True, default=False)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('draft_declaration', 'Tờ khai nháp'),
        ('wait_confirm', 'Chờ xác nhận'),
        ('eligible', 'Đủ điều kiện khai báo'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
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
    brand = fields.Text(string='Nhãn hiệu', tracking=True)
    material = fields.Text(string='Chất liệu', tracking=True)
    model = fields.Text(string='Model', tracking=True)

    picking_count = fields.Integer('Picking Count', compute="_compute_picking_count")
    is_history = fields.Boolean(string='History', default=False, tracking=True)

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

    def action_wait_confirm(self):
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
            self.dpt_exchange_rate = self.product_history_id.dpt_exchange_rate
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
            self.dpt_exchange_rate = self.sale_line_id.payment_exchange_rate
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
        self.product_id.dpt_exchange_rate = self.dpt_exchange_rate
        self.product_id.hs_code_id = self.hs_code_id
        self.product_id.dpt_uom1_id = self.dpt_uom1_id
        self.product_id.dpt_sl1 = self.dpt_sl1
        self.product_id.dpt_sl2 = self.dpt_sl2

    def action_update_eligible(self):
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
                self.dpt_exchange_rate = self.product_id.dpt_exchange_rate
                self.dpt_uom1_id = self.product_id.dpt_uom1_id
                self.dpt_sl1 = self.product_id.dpt_sl1
                self.dpt_sl2 = self.product_id.dpt_sl2
