from odoo import http
import logging

_logger = logging.getLogger(__name__)


class ZaloController(http.Controller):
    @http.route('/zalo/callback', type='http', auth='public')
    def zalo_callback(self, **kwargs):
        code = kwargs.get('code')
        if code:
            # Lấy access token sử dụng mã code
            access_token = self.env['base.automation'].get_access_token(code)
            _logger.info("TOKENT>>>>>>>>>>>>>>>>>>>")
            _logger.info(access_token)
            return http.Response(f"Access Token: {access_token}")
        return http.Response("No code found")
