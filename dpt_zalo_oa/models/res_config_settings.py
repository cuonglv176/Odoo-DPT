import requests
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zalo_app_id = fields.Char(string="Zalo App ID")
    zalo_secret_key = fields.Char(string="Zalo Secret Key")
    zalo_redirect_uri = fields.Char(string="Zalo Redirect URI")
    zalo_authorization_code = fields.Char(string="Zalo Authorization Code")
    zalo_access_token = fields.Char(string="Zalo Access Token", readonly=True)
    zalo_refresh_token = fields.Char(string="Zalo Refresh Token", readonly=True)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            zalo_app_id=self.env['ir.config_parameter'].sudo().get_param('zalo_app_id'),
            zalo_secret_key=self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key'),
            zalo_redirect_uri=self.env['ir.config_parameter'].sudo().get_param('zalo_redirect_uri'),
            zalo_authorization_code=self.env['ir.config_parameter'].sudo().get_param('zalo_authorization_code'),
            zalo_access_token=self.env['ir.config_parameter'].sudo().get_param('zalo_access_token'),
            zalo_refresh_token=self.env['ir.config_parameter'].sudo().get_param('zalo_refresh_token')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('zalo_app_id', self.zalo_app_id)
        self.env['ir.config_parameter'].sudo().set_param('zalo_secret_key', self.zalo_secret_key)
        self.env['ir.config_parameter'].sudo().set_param('zalo_redirect_uri', self.zalo_redirect_uri)
        self.env['ir.config_parameter'].sudo().set_param('zalo_authorization_code', self.zalo_authorization_code)
        self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', self.zalo_access_token)
        self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', self.zalo_refresh_token)

    # Hàm gọi API để lấy access token từ authorization code
    def get_access_token(self):
        app_id = self.zalo_app_id
        secret_key = self.zalo_secret_key
        authorization_code = self.zalo_authorization_code
        redirect_uri = self.zalo_redirect_uri

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
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', refresh_token)
            return data
        else:
            raise ValueError("Error getting access token: " + response.text)

    # Hàm gọi API để làm mới access token
    def refresh_access_token(self):
        app_id = self.zalo_app_id
        secret_key = self.zalo_secret_key
        refresh_token = self.zalo_refresh_token

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
            refresh_token = data.get('refresh_token')
            self.env['ir.config_parameter'].sudo().set_param('zalo_access_token', access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo_refresh_token', refresh_token)
            return data
        else:
            raise ValueError("Error refreshing access token: " + response.text)
