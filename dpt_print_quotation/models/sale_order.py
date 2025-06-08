# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_quotation(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.quotation.print.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id
            },
        }
