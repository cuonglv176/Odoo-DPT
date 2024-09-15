from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ZaloServerActionsParam(models.Model):
    _name = 'zalo.actions.server.params'
    _description = 'Zalo Server Action Param'

    actions_server_id = fields.Many2one('ir.actions.server', string='Actions Server')
    name = fields.Char(string='Name')
    require = fields.Boolean(string='Require')
    fields_id = fields.Many2one('ir.model.fields', string='Get Data By Fields')
    model_id = fields.Many2one('ir.model',related='actions_server_id.model_id')
