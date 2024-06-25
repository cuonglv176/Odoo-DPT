# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api


class DptExportImport(models.Model):
    _name = "dpt.export.import"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import'

    name = fields.Char(string='Title')
    code = fields.Char(string='Code')
    user_id = fields.Many2one('res.users', string='User Export/Import', default=lambda self: self.env.user)
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    line_ids = fields.One2many('dpt.export.import.line', 'export_import_id', string='Export/Import Line')
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft')
    sale_id = fields.Many2one('sale.order', string='Sale Order')


class DptExportImportLine(models.Model):
    _name = "dpt.export.import.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import line'

    sequence = fields.Integer(default=1)
    export_import_id = fields.Many2one('dpt.export.import', string='Export import')
    sale_id = fields.Many2one('sale.order', string='Sale order')
    sale_line_id = fields.Many2one('sale.order.line', string='Sale order line', domain=[('order_id', '=', 'sale_id')])
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id')
    product_id = fields.Many2one('product.product', string='Product')
    package_ids = fields.Many2many('purchase.order.line.package', string='Package')
    dpt_english_name = fields.Char(string='English name', tracking=True)
    dpt_description = fields.Text(string='Description Product', size=240, tracking=True)
    dpt_n_w_kg = fields.Char(string='N.W (KG)', tracking=True)
    dpt_g_w_kg = fields.Char(string='G.W (KG)', tracking=True)
    dpt_uom_id = fields.Many2one('uom.uom', string='Uom Export/Import', tracking=True)
    dpt_uom2_ecus_id = fields.Many2one('uom.uom', string='ĐVT SL2 (Ecus)', tracking=True)
    dpt_uom2_id = fields.Many2one('uom.uom', string='ĐVT 2', tracking=True)
    dpt_price_kd = fields.Monetary(string='Giá KD/giá cũ', tracking=True)
    dpt_price_usd = fields.Monetary(string='Giá khai (USD)', tracking=True)
    dpt_tax_import = fields.Float(string='Tax import (%)', tracking=True)
    dpt_tax_ecus5 = fields.Float(string='VAT ECUS5', tracking=True)
    dpt_tax = fields.Float(string='VAT(%)', tracking=True)
    dpt_exchange_rate = fields.Monetary(string='Exchange rate', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('eligible', 'Đủ điều kiện khai báo'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft')

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
