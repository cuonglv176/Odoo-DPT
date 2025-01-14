from odoo import models, fields

class ImportBrand(models.Model):
    _name = "dpt.import.brand"
    _description = "Import Brand"

    name = fields.Char("Brand Name", required=True)
