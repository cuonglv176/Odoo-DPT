from odoo import models, fields

class PartnerExtension(models.Model):
    _inherit = "res.partner"

    is_buyer = fields.Boolean("Is Buyer")
    is_seller = fields.Boolean("Is Seller")
