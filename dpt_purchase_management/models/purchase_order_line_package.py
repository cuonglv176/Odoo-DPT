from odoo import fields, models, api, _


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

    total_weight = fields.Float('Total Weight (kg)', tracking=True, digits=(12, 0))
    total_volume = fields.Float('Total Volume (m3)', tracking=True, digits=(12, 2))
    note = fields.Text('Note', tracking=True)
    image = fields.Binary(string='Image')
    detail_ids = fields.One2many('purchase.order.line.package.detail', 'package_id', 'Package detail', tracking=True)

    # @api.model
    # def create(self, vals):
    #     if vals.get('code', 'NEW') == 'NEW':
    #         vals['code'] = self._generate_service_code()
    #     return super(PurchaseOrderLinePackage, self).create(vals)

    # def _generate_service_code(self):
    #     sequence = self.env['ir.sequence'].next_by_code('purchase.order.line.package') or '00'
    #     return f'{sequence}'

    @api.constrains('quantity', 'uom_id')
    def constrains_package_name(self):
        for item in self:
            item.code = f"{item.quantity}{item.uom_id.packing_code}"

    @api.onchange('length', 'width', 'height')
    def onchange_size(self):
        self.volume = self.length * self.width * self.height / 1000000

    @api.onchange('quantity', 'volume')
    def onchange_volume(self):
        self.total_volume = self.quantity * self.volume

    @api.onchange('quantity', 'weight')
    def onchange_height(self):
        self.total_weight = self.weight * self.quantity
