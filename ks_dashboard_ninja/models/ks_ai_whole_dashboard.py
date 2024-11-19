import json
import logging
import requests
from odoo import  http, api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class KsAIDashboardninja(models.TransientModel):
    _name = 'ks_dashboard_ninja.ai_dashboard'
    _description = 'AI Dashboard'

    ks_import_model_id = fields.Many2one('ir.model', string='Model',
                                  domain="[('access_ids','!=',False),('transient','=',False),"
                                         "('model','not ilike','base_import%'),('model','not ilike','ir.%'),"
                                         "('model','not ilike','web_editor.%'),('model','not ilike','web_tour.%'),"
                                         "('model','!=','mail.thread'),('model','not ilike','ks_dash%'),('model','not ilike','ks_to%')]",
                                  help="Data source to fetch and read the data for the creation of dashboard items. ", required=True)

    ks_dash_name = fields.Char(string="Dashboard Name", required=True)
    ks_menu_name = fields.Char(string="Menu Name", required=True)
    ks_top_menu_id = fields.Many2one('ir.ui.menu',
                                     domain="[('parent_id','=',False)]",
                                     string="Show Under Menu", required=True,
                                     default=lambda self: self.env['ir.ui.menu'].search(
                                         [('name', '=', 'My Dashboard')])[0])
    ks_template = fields.Many2one('ks_dashboard_ninja.board_template',
                                  default=lambda self: self.env.ref('ks_dashboard_ninja.ks_blank',
                                                                    False),
                                  string="Dashboard Template")

    def ks_do_action(self):
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json",
                   "Catch-Control": "no-cache",
                   }

        if self.ks_import_model_id:
            ks_model_name = self.ks_import_model_id.model
            ks_fields = self.env[ks_model_name].fields_get()
            ks_filtered_fields = {key: val for key, val in ks_fields.items() if val['type'] not in ['many2many', 'one2many', 'binary'] and val['name'] != 'id' and val['name'] != 'sequence' and val['store'] == True}
            ks_fields_name = {val['name']:val['type'] for val in ks_filtered_fields.values()}
            question = ("columns: "+ f"{ks_fields_name}")

            api_key = self.env['ir.config_parameter'].sudo().get_param(
                'ks_dashboard_ninja.dn_api_key')
            url = self.env['ir.config_parameter'].sudo().get_param(
                'ks_dashboard_ninja.url')
            if api_key and url:
                json_data = {'name': api_key,
                            'question':question,
                             'url':self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                            'db_name':self.env.cr.dbname
                        }
                url = url+"/api/v1/ks_dn_main_api"
                ks_ai_response = requests.post(url, data=json_data)
                if ks_ai_response.status_code == 200:
                    ks_ai_response = json.loads(ks_ai_response.text)
                    ks_create_record = self.env['ks_dashboard_ninja.board'].create({
                        'name': self.ks_dash_name,
                        'ks_dashboard_menu_name': self.ks_menu_name,
                        'ks_dashboard_default_template': self.ks_template.id,
                        'ks_dashboard_top_menu_id': self.ks_top_menu_id.id,
                    })
                    ks_dash_id = ks_create_record.id

                    ks_result = self.env['ks_dashboard_ninja.item'].create_ai_dash(ks_ai_response, ks_dash_id,
                                                                                   ks_model_name)

                    if (ks_result == "success"):
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'reload',
                        }
                    else:
                        self.env['ks_dashboard_ninja.board'].browse(ks_dash_id).unlink()
                        raise ValidationError(_("Items didn't render, please try again!"))
                else:
                    raise ValidationError(_("AI Responds with the following status:- %s") % ks_ai_response.text)
            else:
                raise ValidationError(_("Please enter URL and API Key in General Settings"))
        else:
            raise ValidationError(_("Please enter the Model"))




