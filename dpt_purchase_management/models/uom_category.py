from odoo import fields, models, api, _


class UomCategory(models.Model):
    _inherit = 'uom.category'

    active = fields.Boolean('Active', default=True)
