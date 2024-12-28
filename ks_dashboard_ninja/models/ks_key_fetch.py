import base64
import logging
import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class KsAIDashboardFetch(models.TransientModel):
    _name = 'ks_dashboard_ninja.fetch_key'
    _description = 'Fetch API key'

    ks_email_id = fields.Char(string="Email ID")
    ks_api_key =fields.Char(string="Generated AI API Key")
    ks_show_api_key = fields.Boolean(string="Show key",default=False)

    def ks_fetch_details(self):
        url = self.env['ir.config_parameter'].sudo().get_param(
                'ks_dashboard_ninja.url')
        if url and self.ks_email_id:
            url = url + "/api/v1/ks_dn_fetch_api"
            json_data = {'email':self.ks_email_id}
            ks_ai_response = requests.post(url,data=json_data)
            if ks_ai_response.status_code == 200:
                ks_ai_response = json.loads(ks_ai_response.text)
                self.ks_api_key = ks_ai_response
                self.ks_show_api_key = True
            else:
                raise ValidationError(_("Error generates with following status %s"),ks_ai_response.status_code)
