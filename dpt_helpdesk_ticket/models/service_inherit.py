from odoo import models, fields, api, _


class DPTService(models.Model):
    _inherit = 'dpt.service.management'

    helpdesk_team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team')
