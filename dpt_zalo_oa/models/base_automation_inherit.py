from odoo import models, fields, api
import requests
import logging
import hashlib
import base64
import os
_logger = logging.getLogger(__name__)


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    type = fields.Selection([
        ('normal', 'Normal'),
        ('notification', 'Notification'),
        ('zalo', 'Zalo'),
    ], default='normal')
    zalo_template_id = fields.Many2one('dpt.zalo.template', string='Template Zalo')

    @api.model
    def generate_code_verifier(self, length=128):
        # Tạo code_verifier ngẫu nhiên
        verifier = base64.urlsafe_b64encode(os.urandom(length)).rstrip(b'=').decode('utf-8')
        return verifier

    @api.model
    def generate_code_challenge(self, code_verifier):
        # Mã hóa code_verifier sang SHA-256
        sha256_digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        # Mã hóa Base64 không padding
        code_challenge = base64.urlsafe_b64encode(sha256_digest).rstrip(b'=').decode('utf-8')
        return code_challenge

    @api.model
    def get_access_token(self, code):
        app_id = self.env['ir.config_parameter'].sudo().get_param('zalo_app_id')
        secret_key = self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key')
        redirect_uri = self.env['ir.config_parameter'].sudo().get_param('zalo_redirect_uri')
        # Tạo code_verifier và code_challenge
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        # Lưu code_verifier vào Odoo để sử dụng sau này
        self.env['ir.config_parameter'].sudo().set_param('zalo_code_verifier', code_verifier)
        # Dữ liệu để yêu cầu lấy access token
        payload = {
            'app_id': app_id,
            'app_secret': secret_key,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,  # Sử dụng code_verifier để xác thực PKCE
        }
        # Gửi yêu cầu đến Zalo API để lấy access token
        response = requests.post(self.access_token_url, data=payload)
        if response.status_code == 200:
            # Lấy access token từ JSON response
            token_data = response.json()
            access_token = token_data.get('access_token')
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            _logger.info(">>>>>>>>>>>>>>>>>>code>>>>>>>>>>>>>>>>>>")
            _logger.info(code)
            _logger.info(response)
            _logger.info(access_token)
            return access_token
        else:
            # Xử lý lỗi nếu có
            print(f"Error fetching access token: {response.text}")
            return None

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

        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            # Lưu lại access_token và refresh_token trong System Parameters và model
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', refresh_token)

            return access_token
        else:
            raise ValueError("Error getting access token: " + response.text)

    def fetch_zalo_templates(self):
        # Lấy access token nếu cần thiết
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo_access_token')
        if not access_token:
            access_token = self.get_access_token()
        # Gọi API để lấy danh sách templates
        url = 'https://api.zaloapp.com/v4/template'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        _logger.info(">>>>>>>>>>>>>>>>>>>>TEMPLATE>>>>>>>>>>>>>>>>")
        _logger.info(access_token)

        response = requests.get(url, headers=headers)
        _logger.info(response)
        if response.status_code == 200:
            templates = response.json().get('data', [])
            for template in templates:
                template_id = template.get('id')
                template_content = template.get('content')
                self.save_zalo_template(template_id, template_content)
        else:
            raise ValueError("Error fetching templates: " + response.text)

    def save_zalo_template(self, template_id, template_content):
        template_obj = self.env['dpt.zalo.template']
        tem_id = template_obj.search([('zalo_template_id', '=', template_id)])
        if not tem_id:
            template_obj.create({
                'name': f'Template {template_id}',
                'zalo_template_id': template_id,
                'zalo_template_content': template_content,
            })
        else:
            tem_id.write({
                'zalo_template_content': template_content,
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
        # Implement code to refresh the Zalo access token
        pass
