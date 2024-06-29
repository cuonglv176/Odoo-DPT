# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api


class DptExportImportGate(models.Model):
    _name = "dpt.export.import.gate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import Gate'

    name = fields.Char(string='Name')


class DptExportImport(models.Model):
    _name = "dpt.export.import"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import'

    def _get_domain_sale_order(self):
        sale_ids = []
        line_ids = self.env['dpt.export.import.line'].search(
            [('state', '!=', 'draft'), ('export_import_id', '=', False)])
        for line_id in line_ids:
            sale_ids.append(line_id.sale_id.id)
        return [('id', 'in', sale_ids)]

    name = fields.Char(string='Title')
    code = fields.Char(string='Code')
    invoice_code = fields.Char(string='Invoice Code')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sale_ids = fields.Many2many('sale.order', string='Select Sale Order', domain=_get_domain_sale_order)
    partner_importer_id = fields.Many2one('res.partner', string='Partner Importer')
    partner_exporter_id = fields.Many2one('res.partner', string='Partner Exporter')
    gate_id = fields.Many2one('dpt.export.import.gate', string='Gate Importer')
    user_id = fields.Many2one('res.users', string='User Export/Import', default=lambda self: self.env.user)
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    consultation_date = fields.Date(string='Consultation date')
    line_ids = fields.One2many('dpt.export.import.line', 'export_import_id', string='Export/Import Line')
    select_line_ids = fields.Many2many('dpt.export.import.line', string='Export/Import Line',
                                       domain=[('export_import_id', '=', False), ('state', '!=', 'draft')])
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Xác nhận tờ khai'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft')
    declaration_flow = fields.Selection([
        ('red', 'Red'),
        ('yellow', 'Yellow'),
        ('green', 'Green')
    ], string='Declaration Flow', default='red')
    dpt_n_w_kg = fields.Integer(string='Total N.W (KG)', compute="_compute_total_sum_line")
    dpt_g_w_kg = fields.Integer(string='Total G.W (KG)', compute="_compute_total_sum_line")
    total_cubic_meters = fields.Integer(string='Total cubic meters')
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
    payment_exchange_rate = fields.Monetary(string='Payment exchange rate', currency_field='currency_id')
    shipping_slip = fields.Char(string='Shipping Slip')
    type_of_vehicle = fields.Char(string='Type of vehicle')
    driver_name = fields.Char(string='Driver Name')
    driver_phone_number = fields.Char(string='Driver Phone Number')
    vehicle_license_plate = fields.Char(string='Vehicle License Plate')

    @api.onchange('sale_ids')
    def onchange_add_declaration_line(self):
        for order_line_id in self.sale_ids:
            if order_line_id.dpt_export_import_line_ids:
                for dpt_export_import_line_id in order_line_id.dpt_export_import_line_ids:
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

    @api.depends('dpt_amount_tax_import', 'dpt_amount_tax')
    def _compute_estimated_total_amount(self):
        for rec in self:
            rec.estimated_total_amount = rec.dpt_amount_tax + rec.dpt_amount_tax_import

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

    sequence = fields.Integer(default=1)
    export_import_id = fields.Many2one('dpt.export.import', string='Export import')
    lot_code = fields.Char(string='Lot code')
    sale_id = fields.Many2one('sale.order', string='Sale order')
    sale_user_id = fields.Many2one('res.users', string='User Sale', related='sale_id.user_id')
    partner_id = fields.Many2one('res.partner', string='Sale Partner', related='sale_id.partner_id')
    sale_line_id = fields.Many2one('sale.order.line', string='Sale order line', domain=[('order_id', '=', 'sale_id')])
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id')
    product_id = fields.Many2one('product.product', string='Product')
    package_ids = fields.Many2many('purchase.order.line.package', string='Package')
    dpt_english_name = fields.Char(string='English name', tracking=True)
    dpt_description = fields.Text(string='Description Product', size=240, tracking=True)
    dpt_n_w_kg = fields.Integer(string='N.W (KG)', tracking=True)
    dpt_g_w_kg = fields.Integer(string='G.W (KG)', tracking=True)
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
    dpt_exchange_rate = fields.Monetary(string='Exchange rate', tracking=True, currency_field='currency_id')
    hs_code_id = fields.Many2one('dpt.export.import.acfta', string='HS Code')
    dpt_code_hs = fields.Char(string='H')
    dpt_sl1 = fields.Integer(string='SL1', tracking=True)
    dpt_uom1_id = fields.Many2one('uom.uom', string='ĐVT 1', tracking=True)
    dpt_sl2 = fields.Integer(string='SL2', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    currency_usd_id = fields.Many2one('res.currency', string='Currency USD', default=1)
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
    dpt_price_usd = fields.Monetary(string='Giá khai (USD)', tracking=True, currency_field='currency_usd_id')
    dpt_total_usd = fields.Monetary(string='Total (USD)', currency_field='currency_usd_id',
                                    compute="_compute_dpt_total_usd")
    dpt_total_usd_vnd = fields.Monetary(string='Total USD (VND)', currency_field='currency_id',
                                        compute="_compute_dpt_total_usd_vnd")
    dpt_total_cny_vnd = fields.Monetary(string='Total CNY (VND)', currency_field='currency_id',
                                        compute="_compute_dpt_total_cny_vnd")
    dpt_price_cny_vnd = fields.Monetary(string='Price CNY (VND)', tracking=True, currency_field='currency_cny_id')
    dpt_tax_other = fields.Float(string='Tax Other (%)', tracking=True)
    dpt_amount_tax_other = fields.Monetary(string='Amount Tax Other', currency_field='currency_id',
                                           compute="_compute_dpt_amount_tax_other")
    dpt_total_vat = fields.Monetary(string='Total VAT', tracking=True, compute="_compute_total_vat",
                                    currency_field='currency_id')
    dpt_total = fields.Monetary(string='Total', tracking=True, currency_field='currency_id')
    dpt_is_new = fields.Boolean(string='Is new', tracking=True, default=False)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('eligible', 'Đủ điều kiện khai báo'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft')
    declaration_type = fields.Selection([
        ('usd', 'USD'),
        ('cny', 'CNY')
    ], string='Declaration type', default='usd')

    def action_unlink(self):
        self.export_import_id = None

    @api.onchange('hs_code_id')
    def get_data_vat_hs_code(self):
        self.dpt_tax = self.hs_code_id.dpt_vat / 100
        self.dpt_tax_import = self.hs_code_id.dpt_acfa / 100

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

    @api.depends('dpt_tax_import', 'dpt_price_cny_vnd', 'declaration_type', 'dpt_total_usd_vnd')
    def _compute_dpt_amount_tax_import(self):
        for rec in self:
            if rec.declaration_type == 'usd':
                rec.dpt_amount_tax_import = rec.dpt_tax_import * rec.dpt_total_usd_vnd
            else:
                rec.dpt_amount_tax_import = rec.dpt_tax_import * rec.dpt_price_cny_vnd

    @api.depends('dpt_tax', 'dpt_price_cny_vnd', 'declaration_type', 'dpt_total_usd_vnd')
    def _compute_dpt_amount_tax(self):
        for rec in self:
            if rec.declaration_type == 'usd':
                rec.dpt_amount_tax = rec.dpt_tax * rec.dpt_total_usd_vnd
            else:
                rec.dpt_amount_tax = rec.dpt_tax * rec.dpt_price_cny_vnd

    @api.depends('dpt_tax_other', 'dpt_price_cny_vnd', 'declaration_type', 'dpt_total_usd_vnd')
    def _compute_dpt_amount_tax_other(self):
        for rec in self:
            if rec.declaration_type == 'usd':
                rec.dpt_amount_tax_other = rec.dpt_tax_other * rec.dpt_total_usd_vnd
            else:
                rec.dpt_amount_tax_other = rec.dpt_tax_other * rec.dpt_price_cny_vnd

    def write(self, vals):
        val_update_sale_line = {}
        if 'dpt_exchange_rate' in vals:
            val_update_sale_line.update({
                'payment_exchange_rate': vals.get('dpt_exchange_rate')
            })
        if 'dpt_tax_import' in vals:
            val_update_sale_line.update({
                'import_tax_rate': vals.get('dpt_tax_import')
            })
        if 'dpt_tax' in vals:
            val_update_sale_line.update({
                'vat_tax_rate': vals.get('dpt_tax')
            })
        if 'dpt_amount_tax_import' in vals:
            val_update_sale_line.update({
                'import_tax_amount': vals.get('dpt_amount_tax_import')
            })
        if 'dpt_amount_tax' in vals:
            val_update_sale_line.update({
                'vat_tax_amount': vals.get('dpt_amount_tax')
            })
        if 'dpt_total_vat' in vals:
            val_update_sale_line.update({
                'total_tax_amount': vals.get('dpt_total_vat')
            })
        if 'hs_code_id' in vals:
            val_update_sale_line.update({
                'hs_code_id': vals.get('hs_code_id')
            })
        res = super(DptExportImportLine, self).write(vals)
        self.sale_line_id.write(val_update_sale_line)
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
