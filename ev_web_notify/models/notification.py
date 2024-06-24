from odoo import models, fields, api


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    type = fields.Selection([
        ('normal', 'Normal'),
        ('notification', 'Notification'),
    ], default='normal')
    message_notification = fields.Text(string='Notification Message')

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)

        return result


