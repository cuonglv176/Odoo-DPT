from odoo import fields, models, api, _


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals_list):
        res = super(MailMessage, self).create(vals_list)
        if res.model and res.model in ('dpt.vehicle.stage.log'):
            obj_data = self.env[res.model].browse(res.res_id)
            res.res_id = obj_data.shipping_slip_id.id
            res.model = 'dpt.shipping.slip'
        return res
