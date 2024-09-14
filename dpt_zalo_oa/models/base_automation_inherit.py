from odoo import models, fields, api
import requests
import logging
import hashlib
import base64
import os
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    type = fields.Selection([
        ('normal', 'Normal'),
        ('notification', 'Notification'),
        ('zalo', 'Zalo'),
    ], default='normal')
    zalo_template_id = fields.Many2one('dpt.zalo.template', string='Template Zalo')

    def fetch_zalo_templates(self):
        """
        Lấy danh sách template Zalo thông qua API, sử dụng access token đã lưu
        """
        zalo_expired_date = self.env['ir.config_parameter'].sudo().get_param('zalo_expired_date')
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo_access_token')
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        zalo_expired_date = datetime.strptime(zalo_expired_date, date_format)
        if zalo_expired_date < datetime.now():
            self.refresh_zalo_access_token()
        if not access_token:
            raise ValueError("Access token not found, please authenticate first.")
        url = "https://business.openapi.zalo.me/template/all?offset=0&limit=100"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'access_token': access_token
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code == 200:
            templates = response.json().get('data', [])
            for template in templates:
                template_id = template.get('templateId')
                template_content = template.get('templateName')
                self.save_zalo_template(template_id, template_content)
        else:
            _logger.error(f"Error fetching templates: {response.text}")
            raise ValueError("Error fetching templates: " + response.text)

    def save_zalo_template(self, template_id, template_content):
        """
        Lưu hoặc cập nhật template Zalo vào database Odoo
        """
        template_obj = self.env['dpt.zalo.template']
        existing_template = template_obj.search([('zalo_template_id', '=', template_id)])
        if not existing_template:
            # Tạo mới nếu template chưa tồn tại
            template_obj.create({
                'name': template_content,
                'zalo_template_id': template_id,
                'zalo_template_content': template_content,
            })
        else:
            # Cập nhật nếu template đã tồn tại
            existing_template.write({
                'zalo_template_content': template_content,
                'name': template_content,
            })

    def send_zalo_notification(self, order):
        # Lấy cấu hình và template từ record action
        config = self.env['ir.config_parameter'].sudo()
        access_token = config.get_param('zalo_access_token')
        if not access_token:
            # Thực hiện làm mới access token nếu cần
            self.refresh_zalo_access_token()
            access_token = config.get_param('zalo_access_token')

        template_id = self.env['ir.config_parameter'].sudo().get_param('zalo_template_id')
        recipient_id = order.partner_id.zalo_user_id  # Giả sử bạn có trường zalo_user_id trên đối tượng khách hàng

        url = 'https://api.zaloapp.com/v4/message'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        data = {
            'recipient': recipient_id,
            'template_id': template_id,
            'data': {
                'order_id': order.name,
                'order_total': order.amount_total,
            },
        }

        response = requests.post(url, json=data, headers=headers)
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
