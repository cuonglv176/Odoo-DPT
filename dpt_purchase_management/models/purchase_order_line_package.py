from odoo import fields, models, api, _


class PurchaseOrderLinePackage(models.Model):
    _name = 'purchase.order.line.package'
    _description = 'Purchase Package'

    purchase_id = fields.Many2one('purchase.order', 'Purchase')
    detail_ids = fields.One2many('purchase.order.line.package.detail', 'package_id', 'Package detail')
    uom_id = fields.Many2one('uom.uom', 'Package Unit', domain="[('is_package_unit', '=', True)]")
    lot_name = fields.Char('Lot Name')
    quantity = fields.Float('Quantity')
    size = fields.Char('Size')
    weight = fields.Float('Weight (kg)')
    volume = fields.Float('Volume (m3)')
    note = fields.Char('Note')
