from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ZaloController(http.Controller):
    @http.route('/zalo/callback', type='http', auth='public', csrf=False)
    def zalo_callback(self, **kwargs):
        code = kwargs.get('code')
        if code:
            # Lấy access token sử dụng mã code
            try:
                access_token = request.env['base.automation'].sudo().get_access_token(code)
                _logger.info("Access Token Retrieved: %s", access_token)
                return request.make_response(f"Access Token: {access_token}")
            except Exception as e:
                _logger.error("Error retrieving access token: %s", str(e))
                return request.make_response(f"Error: {str(e)}", status=500)
        _logger.warning("No code found in the callback")
        return request.make_response("No code found", status=400)
