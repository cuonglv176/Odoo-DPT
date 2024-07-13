# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dpt_export_import_ids = fields.One2many('dpt.export.import', 'sale_id', string='Declaration')
    dpt_export_import_line_ids = fields.One2many('dpt.export.import.line', 'sale_id', string='Declaration line')
    declaration_count = fields.Integer(string='Declaration count', compute="_compute_declaration_count")
    declaration_line_count = fields.Integer(string='Declaration count line', compute="_compute_declaration_count")
    is_declaration = fields.Boolean(default=False, compute="_compute_is_declaration", store=True)

    @api.depends('dpt_export_import_line_ids', 'dpt_export_import_line_ids.state')
    def _compute_is_declaration(self):
        for rec in self:
            is_declaration = True
            for dpt_export_import_line_id in rec.dpt_export_import_line_ids:
                if dpt_export_import_line_id.state == 'draft':
                    is_declaration = False
                if dpt_export_import_line_id.export_import_id:
                    is_declaration = False
            if not rec.dpt_export_import_line_ids:
                is_declaration = False
            rec.is_declaration = is_declaration

    def _compute_declaration_count(self):
        for rec in self:
            rec.declaration_count = len(rec.dpt_export_import_ids)
            rec.declaration_line_count = len(rec.dpt_export_import_line_ids)

    def action_open_declaration(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_tree').id
        view_form_id = self.env.ref('dpt_export_import.view_dpt_export_import_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.export.import',
            'name': _('Declaration'),
            'view_mode': 'tree,form',
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
            'context': {
                'default_sale_id': self.id,
            },
        }

    def action_open_declaration_line(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_tree').id
        view_form_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.export.import.line',
            'name': _('Declaration Line'),
            'view_mode': 'tree,form',
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    dpt_export_import_line_ids = fields.One2many('dpt.export.import.line', 'sale_line_id', string='Declaration line')
    hs_code_id = fields.Many2one('dpt.export.import.acfta', string='HS Code')
    dpt_code_hs = fields.Char(string='H')
    declared_unit_price = fields.Monetary(string='Declared unit price', currency_field='currency_id',
                                          compute="compute_declared_unit_price")
    declared_unit_total = fields.Monetary(string='Declared unit Total', currency_field='currency_id',
                                          compute="compute_declared_unit_total")
    payment_exchange_rate = fields.Monetary(string='Payment exchange rate', currency_field='currency_id')
    import_tax_rate = fields.Float(string='Import tax rate(%)')
    vat_tax_rate = fields.Float(string='VAT rate(%)')
    other_tax_rate = fields.Float(string='Other tax rate(%)')
    import_tax_amount = fields.Monetary(string='Import tax Amount', currency_field='currency_id')
    vat_tax_amount = fields.Monetary(string='VAT tax Amount', currency_field='currency_id')
    other_tax_amount = fields.Monetary(string='Other tax Amount', currency_field='currency_id')
    total_tax_amount = fields.Monetary(string='Total tax Amount', currency_field='currency_id',
                                       compute="compute_total_tax_amount")
    currency_cny_id = fields.Many2one('res.currency', string='Currency CNY', default=6)
    price_unit_cny = fields.Monetary(string='Price Unit CNY', currency_field='currency_cny_id')
    state_export_import_line = fields.Selection([
        ('draft', 'Nháp'),
        ('eligible', 'Đủ điều kiện khai báo'),
        ('declared', 'Tờ khai thông quan'),
        ('released', 'Giải phóng'),
        ('consulted', 'Tham vấn'),
        ('post_control', 'Kiểm tra sau thông quan'),
        ('cancelled', 'Huỷ')
    ], string='State', default='draft', compute='compute_state_export_import_line')

    @api.onchange('price_unit_cny', 'product_uom_qty')
    def onchange_price_unit_cny(self):
        if self.price_unit_cny != 0:
            self.price_unit = self.price_unit_cny * self.currency_cny_id.rate

    @api.depends('dpt_export_import_line_ids', 'dpt_export_import_line_ids.dpt_price_usd',
                 'dpt_export_import_line_ids.dpt_price_cny_vnd',
                 'dpt_export_import_line_ids.dpt_exchange_rate',
                 'dpt_export_import_line_ids.declaration_type')
    def compute_declared_unit_price(self):
        for rec in self:
            declared_unit_price = 0
            for line in rec.dpt_export_import_line_ids:
                if line.declaration_type == 'usd':
                    declared_unit_price += line.dpt_price_usd * line.dpt_exchange_rate
                if line.declaration_type == 'cny':
                    declared_unit_price += line.dpt_price_cny_vnd * line.dpt_exchange_rate
            rec.declared_unit_price = declared_unit_price

    @api.depends('dpt_export_import_line_ids', 'dpt_export_import_line_ids.dpt_total_usd_vnd',
                 'dpt_export_import_line_ids.dpt_total_cny_vnd', 'dpt_export_import_line_ids.dpt_total_vat',
                 'dpt_export_import_line_ids.declaration_type')
    def compute_declared_unit_total(self):
        for rec in self:
            declared_unit_total = 0
            for line in rec.dpt_export_import_line_ids:
                if line.declaration_type == 'usd':
                    declared_unit_total += line.dpt_total_usd_vnd + line.dpt_total_vat
                if line.declaration_type == 'cny':
                    declared_unit_total += line.dpt_total_cny_vnd + line.dpt_total_vat
            rec.declared_unit_total = declared_unit_total

    @api.depends('import_tax_amount', 'other_tax_amount', 'vat_tax_amount')
    def compute_total_tax_amount(self):
        for rec in self:
            rec.total_tax_amount = rec.import_tax_amount + rec.other_tax_amount + rec.vat_tax_amount

    @api.depends('dpt_export_import_line_ids', 'dpt_export_import_line_ids.state')
    def compute_state_export_import_line(self):
        for rec in self:
            state_export_import_line = 'draft'
            for dpt_export_import_line_id in rec.dpt_export_import_line_ids:
                state_export_import_line = dpt_export_import_line_id.state
            rec.state_export_import_line = state_export_import_line

    @api.onchange('declared_unit_price', 'product_uom_qty')
    def onchange_compute_declared_unit_total(self):
        self.declared_unit_total = self.declared_unit_price * self.product_uom_qty

    @api.onchange('product_id')
    def onchange_compute_tax_rate(self):
        self.import_tax_rate = self.product_id.dpt_tax_import
        self.vat_tax_rate = self.product_id.dpt_tax

    @api.onchange('import_tax_amount', 'declared_unit_total')
    def onchange_compute_import_tax_amount(self):
        self.import_tax_amount = self.declared_unit_total * self.import_tax_amount

    @api.onchange('other_tax_rate', 'declared_unit_total')
    def onchange_compute_other_tax_amount(self):
        self.other_tax_amount = self.declared_unit_total * self.other_tax_rate

    @api.onchange('other_tax_amount', 'import_tax_amount', 'declared_unit_total', 'vat_tax_rate')
    def onchange_compute_vat_tax_amount(self):
        self.vat_tax_amount = (
                                      self.declared_unit_total + self.other_tax_amount + self.import_tax_amount) * self.vat_tax_rate

    def action_open_dpt_export_import_line(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_form').id
        if not self.dpt_export_import_line_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Update Declaration Line'),
                'view_mode': 'form',
                'res_model': 'dpt.export.import.line',
                'target': 'new',
                'views': [[view_id, 'form']],
                'context': {
                    'default_sale_line_id': self.id,
                    'default_sale_id': self.order_id.id,
                    'default_product_id': self.product_id.id,
                    'default_dpt_english_name': self.product_id.dpt_english_name,
                    'default_dpt_description': self.product_id.dpt_description,
                    'default_dpt_n_w_kg': self.product_id.dpt_n_w_kg,
                    'default_dpt_g_w_kg': self.product_id.dpt_g_w_kg,
                    'default_dpt_uom_id': self.product_id.dpt_uom_id,
                    'default_dpt_uom2_ecus_id': self.product_id.dpt_uom2_ecus_id,
                    'default_dpt_uom2_id': self.product_id.dpt_uom2_id,
                    'default_dpt_price_kd': self.product_id.dpt_price_kd,
                    'default_dpt_tax_import': self.import_tax_rate,
                    'default_dpt_amount_tax_import': self.import_tax_amount,
                    'default_dpt_tax_other': self.other_tax_rate,
                    'default_dpt_amount_tax_other': self.other_tax_amount,
                    'default_dpt_tax_ecus5': self.product_id.dpt_tax_ecus5,
                    'default_dpt_tax': self.vat_tax_rate,
                    'default_dpt_amount_tax': self.vat_tax_amount,
                    'default_dpt_exchange_rate': self.payment_exchange_rate,
                    'default_dpt_uom1_id': self.product_uom,
                    'default_dpt_sl1': self.product_uom_qty,
                    'default_dpt_sl2': self.product_id.dpt_sl2,
                    'default_hs_code_id': self.hs_code_id.id,
                },
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Update Declaration Line'),
                'view_mode': 'form',
                'res_model': 'dpt.export.import.line',
                'target': 'new',
                'res_id': self.dpt_export_import_line_ids[0].id,
                'views': [[view_id, 'form']],
            }
