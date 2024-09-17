import requests
from odoo import models, fields, api
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)
import json


class DptZaloTemplate(models.Model):
    _name = 'dpt.zalo.template'
    _description = 'Zalo Template for ZNS'

    name = fields.Char(string="Template Name")
    zalo_app_id = fields.Char(string="Zalo App ID", readonly=True)
    zalo_template_id = fields.Char(string="Zalo Template ID", readonly=True)
    zalo_template_content = fields.Text(string="Template Content", readonly=True)
    zalo_list_params = fields.Json(string='List Params')

    def action_send_zalo_notification(self, records, template_id, recipient, params):
        if records:
            for record_id in records:
                self.send_zalo_notification(record_id, template_id, recipient, params)

    def send_zalo_notification(self, record_id, template_id, recipient, params):
        # Lấy cấu hình và template từ record action
        config = self.env['ir.config_parameter'].sudo()
        zalo_expired_date = self.env['ir.config_parameter'].sudo().get_param('zalo_expired_date')
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo_access_token')
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        zalo_expired_date = datetime.strptime(zalo_expired_date, date_format)
        if zalo_expired_date < datetime.now():
            self.refresh_zalo_access_token()
        if not access_token:
            raise ValueError("Access token not found, please authenticate first.")

        # recipient_id = record_id.recipient.phone
        recipient_id = f'84967121669'
        if recipient.startswith('0'):
            recipient = '84' + recipient[1:]

        url = "https://business.openapi.zalo.me/message/template"
        payload = json.dumps({
            "phone": recipient_id,
            "template_id": template_id,
            "template_data": params,
            "tracking_id": "tracking_id"
        })
        _logger.info(">>>>>>>>>>>>SEND NOTI ZALO ZNS<<<<<<<<<<<<<<<")
        _logger.info(payload)
        headers = {
            'Content-Type': 'application/json',
            'access_token': access_token
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        _logger.info(response.text)
        record_id.message_post(
            body=f"<p><b style='font-weight: 700 !important'>SEND ZALO NOTI:</b> {str(payload)}</p>"
                 f"<p><b style='font-weight: 700 !important'>RESPONSE</b> {response.text}</p>",
            message_type="notification",
        )
        if response.status_code != 200:
            raise ValueError("Error sending Zalo notification: " + response.text)

    def refresh_zalo_access_token(self):
        url = "https://oauth.zaloapp.com/v4/oa/access_token"
        refresh_token = self.env['ir.config_parameter'].sudo().get_param('zalo_refresh_token')
        app_id = self.env['ir.config_parameter'].sudo().get_param('zalo_app_id')
        secret_key = self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key')
        payload = f'refresh_token={refresh_token}&app_id={app_id}&grant_type=refresh_token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'secret_key': secret_key
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in')
            try:
                expires_in = int(expires_in)  # Ensure expires_in is an integer
            except ValueError:
                _logger.error(f"Invalid expires_in value: {expires_in}")
                return None
            zalo_expired_date = datetime.now() + timedelta(seconds=expires_in)
            # Lưu access_token để sử dụng sau này
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', refresh_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_expired_date', str(zalo_expired_date))
            return access_token
        else:
            _logger.error(f"Error fetching access token: {response.text}")
            return None
