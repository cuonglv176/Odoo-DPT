from odoo import fields, models, api, _


class PurchaseOrderLinePackage(models.Model):
    _name = 'purchase.order.line.package'
    _description = 'Purchase Package'

    purchase_id = fields.Many2one('purchase.order', 'Purchase')
    lot_name = fields.Char('Lot Name')
    quantity = fields.Integer('Quantity')
    size = fields.Char('Size')
    weight = fields.Float('Weight (kg)')
    volume = fields.Float('Volume (m3)')
    note = fields.Char('Note')
