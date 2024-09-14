import requests
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class DptZaloTemplate(models.Model):
    _name = 'dpt.zalo.template'
    _description = 'Zalo Template for ZNS'

    name = fields.Char(string="Template Name")
    zalo_app_id = fields.Char(string="Zalo App ID", readonly=True)
    zalo_secret_key = fields.Char(string="Zalo Secret Key", readonly=True)
    zalo_access_token = fields.Char(string="Zalo Access Token", readonly=True)
    zalo_refresh_token = fields.Char(string="Zalo Refresh Token", readonly=True)
    zalo_template_id = fields.Char(string="Zalo Template ID", readonly=True)
    zalo_template_content = fields.Text(string="Template Content", readonly=True)

    @api.model
    def get_zalo_tokens(self):
        # Lấy thông tin cấu hình từ System Parameters
        app_id = self.env['ir.config_parameter'].sudo().get_param('zalo_app_id')
        secret_key = self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key')
        authorization_code = self.env['ir.config_parameter'].sudo().get_param('zalo_authorization_code')
        redirect_uri = self.env['ir.config_parameter'].sudo().get_param('zalo_redirect_uri')

        # Gọi API để lấy access token
        url = 'https://oauth.zaloapp.com/v4/access_token'
        payload = {
            'app_id': app_id,
            'app_secret': secret_key,
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
        }

        response = requests.post(url, data=payload)
        _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(payload)
        _logger.info(response)
        _logger.info(response.status_code)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')

            # Lưu lại access_token và refresh_token trong System Parameters và model
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', refresh_token)
            self.write({
                'zalo_access_token': access_token,
                'zalo_refresh_token': refresh_token
            })
            return access_token
        else:
            raise ValueError("Error getting access token: " + response.text)

    @api.model
    def refresh_zalo_access_token(self):
        # Lấy thông tin cấu hình từ System Parameters
        app_id = self.env['ir.config_parameter'].sudo().get_param('zalo_app_id')
        secret_key = self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key')
        refresh_token = self.env['ir.config_parameter'].sudo().get_param('zalo_refresh_token')

        # Gọi API để làm mới access token
        url = 'https://oauth.zaloapp.com/v4/access_token'
        payload = {
            'app_id': app_id,
            'app_secret': secret_key,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        response = requests.post(url, data=payload)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            new_refresh_token = data.get('refresh_token')

            # Lưu lại access_token và refresh_token trong System Parameters và model
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', new_refresh_token)
            self.write({
                'zalo_access_token': access_token,
                'zalo_refresh_token': new_refresh_token
            })
        else:
            raise ValueError("Error refreshing access token: " + response.text)

    @api.model
    def save_zalo_template(self, template_id, template_content):
        self.create({
            'name': f'Template {template_id}',
            'zalo_template_id': template_id,
            'zalo_template_content': template_content,
        })

    @api.model
    def fetch_zalo_templates(self):
        # Lấy access token nếu cần thiết
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo_access_token')
        if not access_token:
            access_token = self.get_zalo_tokens()
        # Gọi API để lấy danh sách templates
        url = 'https://api.zaloapp.com/v4/template'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            templates = response.json().get('data', [])
            for template in templates:
                template_id = template.get('id')
                template_content = template.get('content')
                self.save_zalo_template(template_id, template_content)
        else:
            raise ValueError("Error fetching templates: " + response.text)
