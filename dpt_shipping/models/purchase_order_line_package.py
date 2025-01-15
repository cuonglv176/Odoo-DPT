# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrderLinePackage(models.Model):
    _inherit = 'purchase.order.line.package'

    transferred_quantity = fields.Float(string='Transferred Quantity')
    transfer_quantity = fields.Float(string='Transfer Quantity')

    @api.constrains('quantity')
    def _constrains_quantity(self):
        for item in self:
            item.transfer_quantity = item.quantity

    @api.onchange('transfer_quantity')
    def onchange_transfer_quantity(self):
        if self.transfer_quantity > self.quantity - self.transferred_quantity:
            raise ValidationError("Vui lòng không điền số lượng lớn hơn số lượng còn lại!")
