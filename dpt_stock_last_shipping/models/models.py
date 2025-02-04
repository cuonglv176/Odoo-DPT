# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class dpt_stock_last_shipping(models.Model):
#     _name = 'dpt_stock_last_shipping.dpt_stock_last_shipping'
#     _description = 'dpt_stock_last_shipping.dpt_stock_last_shipping'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

