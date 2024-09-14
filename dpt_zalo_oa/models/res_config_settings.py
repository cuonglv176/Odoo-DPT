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
    zalo_expired_date = fields.Char(string="Expired Date", readonly=True)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            zalo_app_id=self.env['ir.config_parameter'].sudo().get_param('zalo_app_id'),
            zalo_secret_key=self.env['ir.config_parameter'].sudo().get_param('zalo_secret_key'),
            zalo_redirect_uri=self.env['ir.config_parameter'].sudo().get_param('zalo_redirect_uri'),
            zalo_authorization_code=self.env['ir.config_parameter'].sudo().get_param('zalo_authorization_code'),
            zalo_access_token=self.env['ir.config_parameter'].sudo().get_param('zalo_access_token'),
            zalo_refresh_token=self.env['ir.config_parameter'].sudo().get_param('zalo_refresh_token'),
            zalo_expired_date=self.env['ir.config_parameter'].sudo().get_param('zalo_expired_date')
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
        self.env['ir.config_parameter'].sudo().set_param('zalo_expired_date', self.zalo_expired_date)
