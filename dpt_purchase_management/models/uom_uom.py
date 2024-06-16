from odoo import fields, models, api, _


class UomUom(models.Model):
    _inherit = 'uom.uom'

    is_package_unit = fields.Boolean('Is Package Unit')
    is_default_package_unit = fields.Boolean('Is Default Package Unit')
