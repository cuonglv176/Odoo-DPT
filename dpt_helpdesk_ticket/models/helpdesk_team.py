from odoo import models, fields, api, _


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    service_type_ids = fields.Many2many('dpt.service.management.type', string='Service Type')
