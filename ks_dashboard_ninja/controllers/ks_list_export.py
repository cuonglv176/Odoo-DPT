
import re
import io
import json
import operator
import logging
from odoo.addons.web.controllers.main import ExportFormat, ExportXlsxWriter
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT , xlsxwriter
import datetime
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import pycompat
from ..common_lib.ks_date_filter_selections import ks_get_date, ks_convert_into_utc, ks_convert_into_local
import os
import pytz
from werkzeug.exceptions import InternalServerError
_logger = logging.getLogger(__name__)


class KsListExport(http.Controller):

    def base(self, data):
        params = json.loads(data)
        # header,list_data = operator.itemgetter('header','chart_data')(params)
        header, list_data, item_id, ks_export_boolean, context, params = operator.itemgetter('header', 'chart_data',
                                                                                             'ks_item_id',
                                                                                             'ks_export_boolean',
                                                                                             'context', 'params')(
            params)
        list_data = json.loads(list_data)
        if ks_export_boolean:
            item = request.env['ks_dashboard_ninja.item'].browse(int(item_id))
            ks_timezone = item._context.get('tz') or item.env.user.tz
            if not ks_timezone:
                ks_tzone = os.environ.get('TZ')
                if ks_tzone:
                    ks_timezone = ks_tzone
                elif os.path.exists('/etc/timezone'):
                    ks_tzone = open('/etc/timezone').read()
                    ks_timezone = ks_tzone[0:-1]
                    try:
                        datetime.now(pytz.timezone(ks_timezone))
                    except Exception as e:
                        _logger.info('Please set the local timezone')

                else:
                    _logger.info('Please set the local timezone')
            orderby = item.ks_sort_by_field.id
            sort_order = item.ks_sort_by_order
            ks_start_date = context.get('ksDateFilterStartDate', False)
            ks_end_date = context.get('ksDateFilterEndDate', False)
            ksDateFilterSelection = context.get('ksDateFilterSelection', False)
            if context.get('allowed_company_ids', False):
                item = item.with_context(allowed_company_ids=context.get('allowed_company_ids'))
            if item.ks_data_calculation_type == 'query':
                query_start_date = item.ks_query_start_date
                query_end_date = item.ks_query_end_date
                ks_query = str(item.ks_custom_query)
            if ks_start_date and ks_end_date:
                ks_start_date = datetime.datetime.strptime(ks_start_date,DEFAULT_SERVER_DATETIME_FORMAT)
                ks_end_date = datetime.datetime.strptime(ks_end_date,DEFAULT_SERVER_DATETIME_FORMAT)
            item = item.with_context(ksDateFilterStartDate=ks_start_date)
            item = item.with_context(ksDateFilterEndDate=ks_end_date)
            item = item.with_context(ksDateFilterSelection=ksDateFilterSelection)

            if item._context.get('ksDateFilterSelection', False):
                ks_date_filter_selection = item._context['ksDateFilterSelection']
                if ks_date_filter_selection == 'l_custom':
                    item = item.with_context(ksDateFilterStartDate=ks_start_date)
                    item = item.with_context(ksDateFilterEndDate=ks_end_date)
                    item = item.with_context(ksIsDefultCustomDateFilter=False)

            else:
                ks_date_filter_selection = item.ks_dashboard_ninja_board_id.ks_date_filter_selection
                item = item.with_context(ksDateFilterStartDate=item.ks_dashboard_ninja_board_id.ks_dashboard_start_date)
                item = item.with_context(ksDateFilterEndDate=item.ks_dashboard_ninja_board_id.ks_dashboard_end_date)
                item = item.with_context(ksDateFilterSelection=ks_date_filter_selection)
                item = item.with_context(ksIsDefultCustomDateFilter=True)

            if ks_date_filter_selection not in ['l_custom', 'l_none']:
                ks_date_data = ks_get_date(ks_date_filter_selection, request, 'datetime')
                item = item.with_context(ksDateFilterStartDate=ks_date_data["selected_start_date"])
                item = item.with_context(ksDateFilterEndDate=ks_date_data["selected_end_date"])

            item_domain = params.get('ks_domain_1', [])
            ks_chart_domain = item.ks_convert_into_proper_domain(item.ks_domain, item,item_domain)
            # list_data = item.ks_fetch_list_view_data(item,ks_chart_domain, ks_export_all=
            if list_data['type'] == 'ungrouped':
                list_data = item.ks_fetch_list_view_data(item, ks_chart_domain, ks_export_all=True)
            elif list_data['type'] == 'grouped':
                list_data = item.get_list_view_record(orderby, sort_order, ks_chart_domain, ks_export_all=True)
            elif item.ks_data_calculation_type == 'query':
                if ks_start_date or ks_end_date:
                    query_start_date = ks_start_date
                    query_end_date = ks_end_date
                ks_query_result = item.ks_get_list_query_result(ks_query, query_start_date, query_end_date, ks_offset=0,
                                                                ks_export_all=True)
                list_data = item.ks_format_query_result(ks_query_result)

        # chart_data['labels'].insert(0,'Measure')
        columns_headers = list_data['label']
        import_data = []

        for dataset in list_data['data_rows']:
            if not list_data['type'] == 'grouped':
                for count, index in enumerate(dataset['ks_column_type']):
                    if index == 'datetime':
                        ks_converted_date = False
                        date_string = dataset['data'][count]
                        if dataset['data'][count]:
                            ks_converted_date = ks_convert_into_local(datetime.datetime.strptime(date_string, '%m/%d/%y %H:%M:%S'),ks_timezone)
                        dataset['data'][count] = ks_converted_date
            for ks_count, val in enumerate(dataset['data']):
                if isinstance(val, (float, int)):
                    if val >= 0:
                        try:
                            ks_precision = item.sudo().env.ref('ks_dashboard_ninja.ks_dashboard_ninja_precision').digits
                        except Exception as e:
                            ks_precision = 2
                        dataset['data'][ks_count] = item.env['ir.qweb.field.float'].sudo().value_to_html(val,
                                                                             {'precision': ks_precision})
            import_data.append(dataset['data'])

        return request.make_response(self.from_data(columns_headers, import_data),
            headers=[('Content-Disposition',
                            content_disposition(self.filename(header))),
                     ('Content-Type', self.content_type)],
            # cookies={'fileToken': token}
                                     )


class KsListExcelExport(KsListExport, http.Controller):

    # Excel needs raw data to correctly handle numbers and date values
    raw_data = True

    @http.route('/ks_dashboard_ninja/export/list_xls', type='http', auth="user")
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
        return 'application/vnd.ms-excel'

    def filename(self, base):
        return base + '.xlsx'

    def from_data(self, fields, rows):
        with ExportXlsxWriter(fields, len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)

        return xlsx_writer.value


class KsListCsvExport(KsListExport, http.Controller):

    @http.route('/ks_dashboard_ninja/export/list_csv', type='http', auth="user")
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
        return base + '.csv'

    def from_data(self, fields, rows):
        fp = io.BytesIO()
        writer = pycompat.csv_writer(fp, quoting=1)

        writer.writerow(fields)

        for data in rows:
            row = []
            for d in data:
                # Spreadsheet apps tend to detect formulas on leading =, + and -
                if isinstance(d, str)    and d.startswith(('=', '-', '+')):
                    d = "'" + d

                row.append(pycompat.to_text(d))
            writer.writerow(row)

        return fp.getvalue()
