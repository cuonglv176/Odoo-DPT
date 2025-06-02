# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    picking_ids = fields.Many2many('stock.picking', string='Pickings')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')

    # def action_create_payments(self):
    #     res = super().action_create_payments()
    #     return res
