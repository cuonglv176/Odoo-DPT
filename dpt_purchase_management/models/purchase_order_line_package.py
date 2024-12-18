from odoo import fields, models, api, _
import math
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderLinePackage(models.Model):
    _name = 'purchase.order.line.package'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Purchase Package'
    _order = 'create_date DESC'
    _rec_name = 'code'

    purchase_id = fields.Many2one('purchase.order', 'Purchase', tracking=True)
    sale_id = fields.Many2one('sale.order', 'Sale Order', tracking=True)
    name = fields.Char('Package Name', tracking=True)
    code = fields.Char('Package Code', default='NEW', copy=False, index=True, tracking=True)
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.context_today(self),
                       tracking=True)
    size = fields.Char('Size', tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Package Unit', domain="[('is_package_unit', '=', True)]", tracking=True)
    quantity = fields.Integer('Quantity', tracking=True)
    length = fields.Float('Length (cm)', tracking=True)
    width = fields.Float('Width (cm)', tracking=True)
    height = fields.Float('Height (cm)', tracking=True)
    weight = fields.Float('Weight (kg)', tracking=True)
    volume = fields.Float('Volume (m3)', tracking=True, digits=(12, 5))

    total_weight = fields.Float('Total Weight (kg)', tracking=True, digits=(12, 2), compute="onchange_weight", store=True)
    total_volume = fields.Float('Total Volume (m3)', tracking=True, digits=(12, 3), compute="onchange_volume", store=True)
    note = fields.Text('Note', tracking=True)
    image = fields.Binary(string='Image')
    detail_ids = fields.One2many('purchase.order.line.package.detail', 'package_id', 'Package detail', tracking=True)

    @api.constrains('quantity', 'uom_id')
    def constrains_package_name(self):
        for item in self:
            item.code = f"{item.quantity}{item.uom_id.packing_code}"

    @api.onchange('length', 'width', 'height')
    def onchange_size(self):
        self.volume = self.length * self.width * self.height / 1000000

    @api.onchange('quantity', 'volume')
    @api.depends('quantity', 'volume')
    def onchange_volume(self):
        if self.env.context.get('get_data_from_incoming', False):
            return
        for item in self:
            item.total_volume = math.ceil(round(item.volume * item.quantity * 100, 4)) / 100

    @api.onchange('quantity', 'weight')
    @api.depends('quantity', 'weight')
    def onchange_weight(self):
        if self.env.context.get('get_data_from_incoming', False):
            return
        for item in self:
            item.total_weight = math.ceil(round(item.weight * item.quantity, 2))
