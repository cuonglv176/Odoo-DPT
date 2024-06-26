from odoo import models, fields, api


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    type = fields.Selection([
        ('normal', 'Normal'),
        ('notification', 'Notification'),
    ], default='normal')
    message_notification = fields.Text(string='Notification Message')
    notification_type = fields.Selection([
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ])
    partner_ids = fields.Many2many('res.partner', string='Partner')

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        if result.type != 'notification':
            return result
        self.env["ir.actions.server"].create({
            "name": "Modify name",
            "base_automation_id": result.id,
            "model_id": result.model_id.id,
            "state": "code",
            "code": f"""
automation_id = env['base.automation'].browse({result.id})
env['mail.message']._push_system_notification(  
    {result.create_uid.id},
    automation_id.partner_ids.ids, automation_id.message_notification,
    '{result.model_id.model}', record.id
)
"""
        })
        return result


