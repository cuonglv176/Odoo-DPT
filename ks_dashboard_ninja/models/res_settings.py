from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
import requests
import json

class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    dn_api_key = fields.Char(string="Dashboard AI API Key",store=True,
                             config_parameter='ks_dashboard_ninja.dn_api_key')
    url = fields.Char(string="URL", store=True,
                      config_parameter="ks_dashboard_ninja.url")
    ks_email_id = fields.Char(string="Email ID",store=True,config_parameter="ks_dashboard_ninja.ks_email_id")

    def Open_wizard(self):
        if self.url and self.ks_email_id:
            try:
                url = self.url + "/api/v1/ks_dn_fetch_api"
                json_data = {'email':self.ks_email_id,
                         'url':self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                         'db_name':self.env.cr.dbname
                            }
                ks_ai_response = requests.post(url,data=json_data)
            except Exception as e:
                raise ValidationError(_("Please enter correct URL"))
            if ks_ai_response.status_code == 200:
                try:
                    ks_ai_response = json.loads(ks_ai_response.text)
                except Exception as e:
                    ks_ai_response = False
                if ks_ai_response == "success":
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'message': 'API key sent on Email ID',
                            'sticky': False,
                        }
                    }
                elif ks_ai_response == 'key already generated':
                    raise ValidationError(
                        _("key already generated.If you need assistance, feel free to contact at sales@ksolves.com"))
                else:
                    raise ValidationError(_("Either you have entered wrong URL path or there is some problem in sending request. If you need assistance, feel free to contact at sales@ksolves.com"))
            else:
                raise ValidationError(_("Some problem in sending request.Please contact at sales@ksolves.com"))
        else:
            raise ValidationError(_("Please enter URL and Email ID"))

