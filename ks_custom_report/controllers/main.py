from odoo import http
from odoo.http import request


class GoogleCalendarController(http.Controller):
    @http.route('/ks_custom_report/get_model_name', type='json', auth='user')
    def get_model_domain(self, model, **kw):
        ks_custom_report = request.env['ks_custom_report.ks_report']

        ks_report_record = ks_custom_report.sudo().search([('ks_cr_model_id.model', '=', model)])

        if not ks_report_record or ks_report_record.ks_cr_query_type == 'custom_query':
            return False

        ks_model = ks_report_record.ks_model_id.model
        domains = kw.get('domain')
        ks_domain = []
        if domains:
            for domain in domains:
                if type(domain).__name__ == 'list':
                    field = domain[0]
                    if field == 'x_name':
                        domain[0] = 'id'
                    elif field == 'id':
                        ks_domain.pop(0)
                        continue
                    else:
                        ks_column = request.env['ir.model.fields'].sudo().search(
                            [('name', '=', field), ('model', '=', model)])
                        ks_column_field = ks_report_record.ks_cr_column_ids.search([('ks_cr_field_id', '=', ks_column.id)])
                        ks_column.ensure_one()
                        domain[0] = ks_column_field.ks_model_field_chan
                ks_domain.append(domain)

        return {
            'name': ks_report_record.ks_model_id.display_name,
            'context': request.env.context,
            'view_type': 'list',
            'view_mode': 'list',
            'domain': ks_domain,
            'views': [[False, 'list'], [False, 'form']],
            'res_model': ks_model,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
