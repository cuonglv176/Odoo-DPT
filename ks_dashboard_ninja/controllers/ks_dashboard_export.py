import io
import json
import operator
import logging

from odoo.addons.web.controllers.main import ExportFormat

from odoo import http
from odoo.http import request
from odoo.http import content_disposition,request
from werkzeug.exceptions import InternalServerError
_logger = logging.getLogger(__name__)


class KsDashboardExport(http.Controller):

    def base(self, data):
        params = json.loads(data)
        header, dashboard_data = operator.itemgetter('header', 'dashboard_data')(params)
        return request.make_response(self.from_data(dashboard_data),
                                     headers=[('Content-Disposition',
                                               content_disposition(self.filename(header))),
                                              ('Content-Type', self.content_type)],
                                     # cookies={'fileToken': token}
                                     )


class KsDashboardJsonExport(KsDashboardExport, http.Controller):

    @http.route('/ks_dashboard_ninja/export/dashboard_json', type='http', auth="user")
    def index(self, data):
        try:
            return self.base(data)
        except Exception as exc:
            _logger.exception("Exception during request handling.")
            payload = json.dumps({
                'code': 200,
                'message': "Odoo Server Error",
                'data': http.serialize_exception(exc)
            })
            raise InternalServerError(payload) from exc

    @property
    def content_type(self):
        return 'text/csv;charset=utf8'

    def filename(self, base):
        return base + '.json'

    def from_data(self, dashboard_data):
        fp = io.StringIO()
        fp.write(json.dumps(dashboard_data))

        return fp.getvalue()

class KsItemJsonExport(KsDashboardExport, http.Controller):

    @http.route('/ks_dashboard_ninja/export/item_json', type='http', auth="user")
    def index(self, data):
        try:
            data = json.loads(data)
            item_id = data["item_id"]
            data['dashboard_data'] = request.env['ks_dashboard_ninja.board'].ks_export_item(item_id)
            data = json.dumps(data)
            return self.base(data)
        except Exception as exc:
            _logger.exception("Exception during request handling.")
            payload = json.dumps({
                'code': 200,
                'message': "Odoo Server Error",
                'data': http.serialize_exception(exc)
            })
            raise InternalServerError(payload) from exc


    @property
    def content_type(self):
        return 'text/csv;charset=utf8'

    def filename(self, base):
        return base + '.json'

    def from_data(self, dashboard_data):
        fp = io.StringIO()
        fp.write(json.dumps(dashboard_data))

        return fp.getvalue()
