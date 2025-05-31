from odoo import http
from odoo.http import request
import json


class FundDashboardController(http.Controller):

    @http.route('/fund/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """API endpoint to get dashboard data"""
        dashboard_model = request.env['fund.dashboard']
        return dashboard_model.get_dashboard_data()

    @http.route('/fund/dashboard/refresh', type='json', auth='user')
    def refresh_dashboard(self):
        """Refresh dashboard data"""
        dashboard = request.env['fund.dashboard'].search([], limit=1)
        if dashboard:
            dashboard._compute_summary()
            dashboard._compute_performance()
            dashboard._compute_charts()
        return {'status': 'success'}
