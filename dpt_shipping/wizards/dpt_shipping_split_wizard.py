# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class DPTShippingSplitWizard(models.TransientModel):
    _name = 'dpt.shipping.split.wizard'

    sale_ids = fields.Many2many('sale.order', string='Sale Order')
    shipping_id = fields.Many2one('dpt.shipping.slip', tring='Shipping Slip')

    def create_shipping_receive(self):
        return
