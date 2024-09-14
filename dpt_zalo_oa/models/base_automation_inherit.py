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
        """
        Tạo một mã code_verifier ngẫu nhiên để sử dụng trong PKCE (Proof Key for Code Exchange)
        """
        verifier = base64.urlsafe_b64encode(os.urandom(length)).rstrip(b'=').decode('utf-8')
        return verifier

    @api.model
    def generate_code_challenge(self, code_verifier):
        """
        Tạo một mã code_challenge từ code_verifier đã được mã hóa SHA-256
        """
        sha256_digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_digest).rstrip(b'=').decode('utf-8')
        return code_challenge

    @api.model
    def get_access_token(self, code):
        """
        Hàm này sẽ thực hiện việc lấy access token từ Zalo bằng cách sử dụng code_verifier và code_challenge
        """
        app_id = self.env['ir.config_parameter'].sudo().get_param('zalo_app_id')
        secret_key = self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key')
        redirect_uri = self.env['ir.config_parameter'].sudo().get_param('zalo_redirect_uri')

        # Tạo code_verifier và code_challenge cho PKCE
        code_verifier = self.generate_code_verifier()
        _logger.info("code_verifier>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(code_verifier)
        code_challenge = self.generate_code_challenge(code_verifier)

        # Lưu code_verifier để dùng cho yêu cầu tiếp theo
        self.env['ir.config_parameter'].sudo().set_param('zalo_code_verifier', code_verifier)

        # Dữ liệu để gửi yêu cầu lấy access token
        payload = {
            'app_id': app_id,
            'app_secret': secret_key,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
        }

        access_token_url = 'https://oauth.zaloapp.com/v4/access_token'  # URL lấy token
        response = requests.post(access_token_url, data=payload)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            # Lưu access_token để sử dụng sau này
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            _logger.info(f"Access token received: {access_token}")
            return access_token
        else:
            _logger.error(f"Error fetching access token: {response.text}")
            return None

    def fetch_zalo_templates(self):
        """
        Lấy danh sách template Zalo thông qua API, sử dụng access token đã lưu
        """
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo_access_token')
        if not access_token:
            raise ValueError("Access token not found, please authenticate first.")

        url = 'https://api.zaloapp.com/v4/template'  # URL API lấy template Zalo
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
                'name': f'Template {template_id}',
                'zalo_template_id': template_id,
                'zalo_template_content': template_content,
            })
        else:
            # Cập nhật nếu template đã tồn tại
            existing_template.write({
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
