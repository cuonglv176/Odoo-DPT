from odoo import models, fields, api, _


class DPTService(models.Model):
    _inherit = 'dpt.service.management'

    helpdesk_team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team')

    @api.model
    def create(self, vals):
        self.env['helpdesk.team'].create({
            'name': vals.get('name'),
            'company_id': 1,
        })
        return super(DPTService, self).create(vals)
