from odoo import http
from datetime import datetime, timedelta
from odoo.http import request
import logging
import hashlib
import base64
import os
import requests  # Import requests to handle HTTP requests

_logger = logging.getLogger(__name__)


class ZaloController(http.Controller):
    @http.route('/zalo/callback', type='http', auth='public', methods=['GET', 'POST'])
    def zalo_callback(self, **kwargs):
        code = kwargs.get('code')
        if code:
            # Lấy access token sử dụng mã code
            try:
                access_token = self.get_access_token(code)
                _logger.info("Access Token Retrieved: %s", access_token)
                return request.make_response(f"Access Token: {access_token}")
            except Exception as e:
                _logger.error("Error retrieving access token: %s", str(e))
                return request.make_response(f"Error: {str(e)}", status=500)
        _logger.warning("No code found in the callback")
        return request.make_response("No code found", status=400)

    def generate_code_verifier(self, length=128):
        """
        Tạo một mã code_verifier ngẫu nhiên để sử dụng trong PKCE (Proof Key for Code Exchange)
        """
        verifier = base64.urlsafe_b64encode(os.urandom(length)).rstrip(b'=').decode('utf-8')
        return verifier

    def generate_code_challenge(self, code_verifier):
        """
        Tạo một mã code_challenge từ code_verifier đã được mã hóa SHA-256
        """
        sha256_digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_digest).rstrip(b'=').decode('utf-8')
        return code_challenge

    def get_access_token(self, code):
        """
        Hàm này sẽ thực hiện việc lấy access token từ Zalo bằng cách sử dụng code_verifier và code_challenge
        """
        app_id = request.env['ir.config_parameter'].sudo().get_param('zalo_app_id')
        secret_key = request.env['ir.config_parameter'].sudo().get_param('zalo_secret_key')
        redirect_uri = request.env['ir.config_parameter'].sudo().get_param('zalo_redirect_uri')

        # Tạo code_verifier và code_challenge cho PKCE
        code_verifier = self.generate_code_verifier()
        _logger.info("code_verifier>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(code_verifier)

        # Lưu code_verifier để dùng cho yêu cầu tiếp theo
        request.env['ir.config_parameter'].sudo().set_param('zalo_code_verifier', code_verifier)

        # Dữ liệu để gửi yêu cầu lấy access token

        url = "https://oauth.zaloapp.com/v4/oa/access_token"
        payload = f'code={code}&app_id={app_id}&grant_type=authorization_code&code_verifier={code_verifier}'
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
            zalo_expired_date = datetime.now() + timedelta(seconds=expires_in)
            # Lưu access_token để sử dụng sau này
            request.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            request.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', refresh_token)
            request.env['ir.config_parameter'].sudo().set_param('zalo_expired_date', zalo_expired_date)
            _logger.info(f"Access token received: {access_token}")
            return access_token
        else:
            _logger.error(f"Error fetching access token: {response.text}")
            return None
