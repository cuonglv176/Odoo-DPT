from odoo import models, fields, api
import requests

class BaseAutomation(models.Model):
    _inherit = 'base.automation'

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
