# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
from odoo.exceptions import AccessError, UserError, ValidationError

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
    _order = 'create_date desc'

    name = fields.Char(string='Title', tracking=True)
    code = fields.Char(string='Code', tracking=True)
    invoice_code = fields.Char(string='Invoice Code', tracking=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sale_ids = fields.Many2many('sale.order', string='Select Sale Order', tracking=True)
    partner_importer_id = fields.Many2one('res.partner', string='Partner Importer')
    partner_exporter_id = fields.Many2one('res.partner', string='Partner Exporter')
    gate_id = fields.Many2one('dpt.export.import.gate', string='Gate Importer')
    user_id = fields.Many2one('res.users', string='User Export/Import', default=lambda self: self.env.user,
                              tracking=True)
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    consultation_date = fields.Date(string='Consultation date')
    line_ids = fields.One2many('dpt.export.import.line', 'export_import_id', string='Export/Import Line')
    select_line_ids = fields.Many2many('dpt.export.import.line', string='Export/Import Line',
                                       domain=[('export_import_id', '=', False), ('state', '!=', 'draft')])
    dpt_tax_ecus5 = fields.Char(string='VAT ECUS5', tracking=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Nháp nội bộ'),
        ('draft_declaration', 'Nháp hải quan'),
        ('wait_confirm', 'Chờ duyệt nội bộ'),
        ('confirm', 'Đồng ý duyệt nội bộ'),
        ('cancelled', 'Từ chối duyệt nội bộ'),
        ('declared', 'Chính Thức'),
        ('edit', 'Sửa'),
        ('released', 'Giải phóng hàng'),
        # ('consulted', 'Tham vấn'),
        ('back_for_stock', 'Mang hàng về bảo quản'),
        ('cleared', 'Thông Quan'),
        ('edit_ama', 'Sửa AMA'),
        # ('post_control', 'Kiểm tra sau thông quan'),
        # ('cancelled', 'Huỷ')
    ], string='State', default='draft', tracking=True)
    # ('draft', 'Nháp'),
    # ('draft_declaration', 'Nháp hải quan'),
    # ('confirm', 'Xác nhận tờ khai'),
    # ('declared', 'Tờ khai thông quan'),
    # ('released', 'Giải phóng'),
    # ('consulted', 'Tham vấn'),
    # ('post_control', 'Kiểm tra sau thông quan'),
    # ('cancelled', 'Huỷ')

    # - Nháp nội bộ *
    # - Nháp hải quan *
    # - Chờ duyệt nội bộ
    # - Đồng ý duyệt nội bộ *
    # - Từ chối duyệt nội bộ*
    # - Chính thức*
    # - Sửa*
    # - Giải phóng hàng*
    # - Mang hàng vè bảo quản*
    # - Thông quan
    # - Sửa AMA

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
    active = fields.Boolean('Active', default=True)

    def action_draft_declaration(self):
        self.state = 'draft_declaration'
        # for line_id in self.line_ids:
        #     line_id.state = 'draft_declaration'

    # ('draft', 'Nháp'),
    # ('draft_declaration', 'Nháp hải quan'),
    # ('wait_confirm', 'Chờ duyệt nội bộ'),
    # ('confirm', 'Đồng ý duyệt nội bộ'),
    # ('cancelled', 'Từ chối duyệt nội bộ'),
    # ('declared', 'Chính Thức'),
    # ('edit', 'Sửa'),
    # ('released', 'Giải phóng hàng'),
    # ('back_for_stock', 'Mang hàng về bảo quản'),
    # ('cleared', 'Thông Quan'),
    # ('edit_ama', 'Sửa AMA'),

    def action_back_to_draft(self):
        self.state = 'draft'

    def action_sent_to_confirm(self):
        self.action_check_lot_name()
        self.state = 'wait_confirm'
        # for line_id in self.line_ids:
        #     line_id.state = 'draft_declaration'

    def action_confirm(self):
        self.action_check_lot_name()
        self.state = 'confirm'

    def action_declared(self):
        self.action_check_lot_name()
        self.state = 'declared'
        # for line_id in self.line_ids:
        #     line_id.state = 'declared'

    def action_edit(self):
        self.action_check_lot_name()
        self.state = 'edit'

    def action_released(self):
        self.action_check_lot_name()
        self.state = 'released'
        # for line_id in self.line_ids:
        #     line_id.state = 'released'

    def action_back_for_stock(self):
        self.action_check_lot_name()
        self.state = 'back_for_stock'

    def action_cleared(self):
        self.action_check_lot_name()
        self.state = 'cleared'
        # for line_id in self.line_ids:
        #     line_id.state = 'consulted'

    # def action_post_control(self):
    #     self.state = 'post_control'
    # for line_id in self.line_ids:
    #     line_id.state = 'post_control'

    def action_edit_ama(self):
        self.action_check_lot_name()
        self.state = 'edit_ama'

    def action_cancelled(self):
        self.state = 'cancelled'
        # for line_id in self.line_ids:
        #     line_id.state = 'cancelled'

    def action_check_lot_name(self):
        check = False
        for line_id in self.line_ids:
            if not line_id.stock_picking_ids:
                check = True
        if check:
            raise UserError(f"Chưa được cập nhật mã lô, vui lòng kiểm tra lại!!!")

        # picking_lot_name_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', 'in', self.ids), ('sale_id', 'in', self.ids),
        #      ('state', '!=', 'cancel'), ('picking_lot_name', '=', False)])
        # if picking_lot_name_ids:
        #     picking_lot_name = ','.join(picking_lot_name_ids.mapped('name'))
        #     raise UserError(f"Vận chuyển : {picking_lot_name} chưa được cập nhật mã lô, vui lòng kiểm tra lại!!!")
        #
        # not_picking_lot_name_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', 'in', self.ids), ('sale_id', 'in', self.ids)])
        # if not not_picking_lot_name_ids:
        #     raise UserError(f"Không có phiếu vận chuyển, vui lòng kiểm tra lại!!!")

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
        if 'payment_exchange_rate' in vals:
            for line_id in self.line_ids:
                line_id.dpt_exchange_rate = self.payment_exchange_rate
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
