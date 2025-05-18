# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_pricelist_ids = fields.One2many('product.pricelist.item', 'partner_id', 
                                           string='Bảng giá dịch vụ',
                                           domain=[('service_id', '!=', False)])