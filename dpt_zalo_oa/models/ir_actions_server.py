from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServerActions(models.Model):
    _name = 'ir.actions.server'
    _description = 'Server Action'
    _inherit = ['ir.actions.server']

    state = fields.Selection(selection_add=[('zalo_zns', 'Zalo ZNS')])
