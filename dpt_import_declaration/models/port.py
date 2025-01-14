from odoo import models, fields

class ImportPort(models.Model):
    _name = "dpt.import.port"
    _description = "Import Port"

    name = fields.Char("Port Name", required=True)
    code = fields.Char("Port Code")
