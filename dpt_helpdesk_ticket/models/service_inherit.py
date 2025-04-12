from odoo import models, fields, api, _


class DPTService(models.Model):
    _inherit = 'dpt.service.management'

    helpdesk_team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team')
    is_tth_service = fields.Boolean(string='TTH Service')
    is_create_ticket_first = fields.Boolean(string='Tạo ticket trước duyệt đơn', default=False)

    @api.model
    def create(self, vals):
        self.env['helpdesk.team'].create({
            'name': vals.get('name'),
            'company_id': 1,
        })
        return super(DPTService, self).create(vals)
