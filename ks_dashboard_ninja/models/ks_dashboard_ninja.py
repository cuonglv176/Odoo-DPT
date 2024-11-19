# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError
import datetime
import json
from odoo.addons.ks_dashboard_ninja.common_lib.ks_date_filter_selections import ks_get_date, ks_convert_into_local, \
    ks_convert_into_utc
from odoo.tools.safe_eval import safe_eval
import locale
from dateutil.parser import parse


class KsDashboardNinjaBoard(models.Model):
    _name = 'ks_dashboard_ninja.board'
    _description = 'Dashboard Ninja'

    name = fields.Char(string="Dashboard Name", required=True, size=35)
    ks_dashboard_items_ids = fields.One2many('ks_dashboard_ninja.item', 'ks_dashboard_ninja_board_id',
                                             string='Dashboard Items')
    ks_dashboard_menu_name = fields.Char(string="Menu Name")
    ks_dashboard_top_menu_id = fields.Many2one('ir.ui.menu',
                                               domain="['|',('action','=',False),('parent_id','=',False)]",
                                               string="Show Under Menu",
                                               default=lambda self: self.env['ir.ui.menu'].search(
                                                   [('name', '=', 'My Dashboard')]))
    ks_dashboard_client_action_id = fields.Many2one('ir.actions.client')
    ks_dashboard_menu_id = fields.Many2one('ir.ui.menu')
    ks_dashboard_state = fields.Char()
    ks_dashboard_active = fields.Boolean(string="Active", default=True)
    ks_dashboard_group_access = fields.Many2many('res.groups', string="Group Access")

    # DateFilter Fields
    ks_dashboard_start_date = fields.Datetime(string="Start Date")
    ks_dashboard_end_date = fields.Datetime(string="End Date")
    ks_date_filter_selection = fields.Selection([
        ('l_none', 'All Time'),
        ('l_day', 'Today'),
        ('t_week', 'This Week'),
        ('t_month', 'This Month'),
        ('t_quarter', 'This Quarter'),
        ('t_year', 'This Year'),
        ('td_week', 'Week to Date'),
        ('td_month', 'Month to Date'),
        ('td_quarter', 'Quarter to Date'),
        ('td_year', 'Year to Date'),
        ('n_day', 'Next Day'),
        ('n_week', 'Next Week'),
        ('n_month', 'Next Month'),
        ('n_quarter', 'Next Quarter'),
        ('n_year', 'Next Year'),
        ('ls_day', 'Last Day'),
        ('ls_week', 'Last Week'),
        ('ls_month', 'Last Month'),
        ('ls_quarter', 'Last Quarter'),
        ('ls_year', 'Last Year'),
        ('l_week', 'Last 7 days'),
        ('l_month', 'Last 30 days'),
        ('l_quarter', 'Last 90 days'),
        ('l_year', 'Last 365 days'),
        ('ls_past_until_now', 'Past Till Now'),
        ('ls_pastwithout_now', ' Past Excluding Today'),
        ('n_future_starting_now', 'Future Starting Now'),
        ('n_futurestarting_tomorrow', 'Future Starting Tomorrow'),
        ('l_custom', 'Custom Filter'),
    ], default='l_none', string="Default Date Filter")

    # for setting Global/Indian Format
    ks_data_formatting = fields.Selection([
        ('global', 'Global'),
        ('indian', 'Indian'),
        ('exact', 'Exact')
    ], string='Format')

    ks_gridstack_config = fields.Char('Item Configurations')
    ks_dashboard_default_template = fields.Many2one('ks_dashboard_ninja.board_template',
                                                    default=lambda self: self.env.ref('ks_dashboard_ninja.ks_blank',
                                                                                      False),
                                                    string="Dashboard Template")

    ks_set_interval = fields.Selection([
        ('15000', '15 Seconds'),
        ('30000', '30 Seconds'),
        ('45000', '45 Seconds'),
        ('60000', '1 minute'),
        ('120000', '2 minute'),
        ('300000', '5 minute'),
        ('600000', '10 minute'),
    ], string="Default Update Interval", help="Update Interval for new items only")
    ks_dashboard_menu_sequence = fields.Integer(string="Menu Sequence", default=10,
                                                help="Smallest sequence give high priority and Highest sequence give "
                                                     "low priority")
    ks_child_dashboard_ids = fields.One2many('ks_dashboard_ninja.child_board', 'ks_dashboard_ninja_id')
    ks_dashboard_defined_filters_ids = fields.One2many('ks_dashboard_ninja.board_defined_filters',
                                                       'ks_dashboard_board_id',
                                                       string='Dashboard Predefined Filters')
    ks_dashboard_custom_filters_ids = fields.One2many('ks_dashboard_ninja.board_custom_filters',
                                                      'ks_dashboard_board_id',
                                                      string='Dashboard Custom Filters')
    multi_layouts = fields.Boolean(string='Enable Multi-Dashboard Layouts',
                                   help='Allow user to have multiple layouts of the same Dashboard')


    @api.constrains('ks_dashboard_start_date', 'ks_dashboard_end_date')
    def ks_date_validation(self):
        for rec in self:
            if rec.ks_dashboard_start_date > rec.ks_dashboard_end_date:
                raise ValidationError(_('Start date must be less than end date'))

    @api.model_create_multi
    def create(self, vals):
        records = super(KsDashboardNinjaBoard, self).create(vals)
        for record in records:
            if record.ks_dashboard_top_menu_id and record.ks_dashboard_menu_name:
                action_id = {
                    'name': record.ks_dashboard_menu_name + " Action",
                    'res_model': 'ks_dashboard_ninja.board',
                    'tag': 'ks_dashboard_ninja',
                    'params': {'ks_dashboard_id': record.id},
                }
                record.ks_dashboard_client_action_id = self.env['ir.actions.client'].sudo().create(action_id)

                record.ks_dashboard_menu_id = self.env['ir.ui.menu'].sudo().create({
                    'name': record.ks_dashboard_menu_name,
                    'active': record.ks_dashboard_active,
                    'parent_id': record.ks_dashboard_top_menu_id.id,
                    'action': "ir.actions.client," + str(record.ks_dashboard_client_action_id.id),
                    'groups_id': record.ks_dashboard_group_access.ids if record.ks_dashboard_group_access else False,
                    'sequence': record.ks_dashboard_menu_sequence if record.ks_dashboard_menu_sequence else 10
                })

            if record.ks_dashboard_default_template and record.ks_dashboard_default_template.ks_item_count:
                ks_gridstack_config = {}
                template_data = json.loads(record.ks_dashboard_default_template.ks_gridstack_config)
                for item_data in template_data:
                    if record.ks_dashboard_default_template.ks_template_type == 'ks_custom':
                        dashboard_item = self.env['ks_dashboard_ninja.item'].browse(int(item_data)).copy(
                            {'ks_dashboard_ninja_board_id': record.id})
                        ks_gridstack_config[dashboard_item.id] = template_data[item_data]
                    else:
                        dashboard_item = self.env.ref(item_data['item_id']).copy({'ks_dashboard_ninja_board_id': record.id})
                        ks_gridstack_config[dashboard_item.id] = item_data['data']
                record.ks_gridstack_config = json.dumps(ks_gridstack_config)
        return records

    @api.onchange('ks_date_filter_selection')
    def ks_date_filter_selection_onchange(self):
        for rec in self:
            if rec.ks_date_filter_selection and rec.ks_date_filter_selection != 'l_custom':
                rec.ks_dashboard_start_date = False
                rec.ks_dashboard_end_date = False

    def write(self, vals):
        if vals.get('ks_date_filter_selection', False) and vals.get('ks_date_filter_selection') != 'l_custom':
            vals.update({
                'ks_dashboard_start_date': False,
                'ks_dashboard_end_date': False

            })
        record = super(KsDashboardNinjaBoard, self).write(vals)
        for rec in self:
            if 'ks_dashboard_menu_name' in vals:
                if self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board') and self.env.ref(
                        'ks_dashboard_ninja.ks_my_default_dashboard_board').sudo().id == rec.id:
                    if self.env.ref('ks_dashboard_ninja.board_menu_root', False):
                        self.env.ref('ks_dashboard_ninja.board_menu_root').sudo().name = vals['ks_dashboard_menu_name']
                else:
                    rec.ks_dashboard_menu_id.sudo().name = vals['ks_dashboard_menu_name']
            if 'ks_dashboard_group_access' in vals:
                if self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board').id == rec.id:
                    if self.env.ref('ks_dashboard_ninja.board_menu_root', False):
                        self.env.ref('ks_dashboard_ninja.board_menu_root').groups_id = vals['ks_dashboard_group_access']
                else:
                    rec.ks_dashboard_menu_id.sudo().groups_id = vals['ks_dashboard_group_access']
            if 'ks_dashboard_active' in vals and rec.ks_dashboard_menu_id:
                rec.ks_dashboard_menu_id.sudo().active = vals['ks_dashboard_active']

            if 'ks_dashboard_top_menu_id' in vals:
                rec.ks_dashboard_menu_id.write(
                    {'parent_id': vals['ks_dashboard_top_menu_id']}
                )

            if 'ks_dashboard_menu_sequence' in vals:
                rec.ks_dashboard_menu_id.sudo().sequence = vals['ks_dashboard_menu_sequence']
            if 'name' in vals:
                rec.ks_dashboard_client_action_id.sudo().name = vals['name']

        return record

    def unlink(self):
        if self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board').id in self.ids:
            raise ValidationError(_("Default Dashboard can't be deleted."))
        else:
            for rec in self:
                rec.ks_dashboard_client_action_id.sudo().unlink()
                rec.ks_child_dashboard_ids.unlink()
                rec.ks_dashboard_menu_id.sudo().unlink()
                rec.ks_dashboard_items_ids.unlink()
        res = super(KsDashboardNinjaBoard, self).unlink()
        return res

    def ks_get_grid_config(self):
        default_grid_id = self.env['ks_dashboard_ninja.child_board'].search(
            [['id', 'in', self.ks_child_dashboard_ids.ids], ['company_id', '=', self.env.company.id],
             ['board_type', '=', 'default']])

        if not default_grid_id:
            default_grid_id = self.env['ks_dashboard_ninja.child_board'].create({
                "ks_gridstack_config": self.ks_gridstack_config,
                "ks_dashboard_ninja_id": self.id,
                "name": "Default Board Layout",
                "company_id": self.env.company.id,
                "board_type": "default",
            })

        return default_grid_id

    @api.model
    def ks_fetch_dashboard_data(self, ks_dashboard_id, ks_item_domain=False):
        """
        Return Dictionary of Dashboard Data.
        :param ks_dashboard_id: Integer
        :param ks_item_domain: List[List]
        :return: dict
        """

        ks_dn_active_ids = []
        if self._context.get('ks_dn_active_ids'):
            ks_dn_active_ids = self._context.get('ks_dn_active_ids')

        ks_dn_active_ids.append(ks_dashboard_id)
        self = self.with_context(
            ks_dn_active_ids=ks_dn_active_ids,
        )

        has_group_ks_dashboard_manager = self.env.user.has_group('ks_dashboard_ninja.ks_dashboard_ninja_group_manager')
        ks_dashboard_rec = self.browse(ks_dashboard_id)
        dashboard_data = {
            'name': ks_dashboard_rec.name,
            'multi_layouts': ks_dashboard_rec.multi_layouts,
            'ks_company_id': self.env.company.id,
            'ks_dashboard_manager': has_group_ks_dashboard_manager,
            'ks_dashboard_list': self.search_read([], ['id', 'name']),
            'ks_dashboard_start_date': self._context.get('ksDateFilterStartDate', False) or self.browse(
                ks_dashboard_id).ks_dashboard_start_date,
            'ks_dashboard_end_date': self._context.get('ksDateFilterEndDate', False) or self.browse(
                ks_dashboard_id).ks_dashboard_end_date,
            'ks_date_filter_selection': self._context.get('ksDateFilterSelection', False) or self.browse(
                ks_dashboard_id).ks_date_filter_selection,
            'ks_gridstack_config': "{}",
            'ks_set_interval': ks_dashboard_rec.ks_set_interval,
            'ks_data_formatting': ks_dashboard_rec.ks_data_formatting,
            'ks_dashboard_items_ids': ks_dashboard_rec.ks_dashboard_items_ids.ids,
            'ks_item_data': {},
            'ks_child_boards': False,
            'ks_selected_board_id': False,
            'ks_dashboard_domain_data': ks_dashboard_rec.ks_prepare_dashboard_domain(),
            'ks_dashboard_pre_domain_filter': ks_dashboard_rec.ks_prepare_dashboard_pre_domain(),
            'ks_dashboard_custom_domain_filter': ks_dashboard_rec.ks_prepare_dashboard_custom_domain(),
            'ks_item_model_relation': dict([(x['id'], [x['ks_model_name'], x['ks_model_name_2']]) for x in
                                            ks_dashboard_rec.ks_dashboard_items_ids.read(
                                                ['ks_model_name', 'ks_model_name_2'])]),
            'ks_model_item_relation': {},
        }

        default_grid_id = ks_dashboard_rec.ks_get_grid_config()
        dashboard_data['ks_gridstack_config'] = default_grid_id[0].ks_gridstack_config
        dashboard_data['ks_gridstack_config_id'] = default_grid_id[0].id

        if self.env['ks_dashboard_ninja.child_board'].search(
                [['id', 'in', ks_dashboard_rec.ks_child_dashboard_ids.ids], ['company_id', '=', self.env.company.id],
                 ['board_type', '!=', 'default']], limit=1):
            dashboard_data['ks_child_boards'] = {
                'ks_default': [ks_dashboard_rec.name, default_grid_id[0].ks_gridstack_config]}
            selecred_rec = self.env['ks_dashboard_ninja.child_board'].search(
                [['id', 'in', ks_dashboard_rec.ks_child_dashboard_ids.ids], ['ks_active', '=', True],
                 ['company_id', '=', self.env.company.id], ['board_type', '!=', 'default']], limit=1)
            if selecred_rec:
                dashboard_data['ks_selected_board_id'] = str(selecred_rec.id)
                dashboard_data['ks_gridstack_config'] = selecred_rec.ks_gridstack_config
            else:
                dashboard_data['ks_selected_board_id'] = 'ks_default'
            for rec in self.env['ks_dashboard_ninja.child_board'].search_read(
                    [['id', 'in', ks_dashboard_rec.ks_child_dashboard_ids.ids],
                     ['company_id', '=', self.env.company.id], ['board_type', '!=', 'default']],
                    ['name', 'ks_gridstack_config']):
                dashboard_data['ks_child_boards'][str(rec['id'])] = [rec['name'], rec['ks_gridstack_config']]
        ks_item_domain = ks_item_domain or []
        try:
            items = self.ks_dashboard_items_ids.search(
                [['ks_dashboard_ninja_board_id', '=', ks_dashboard_id]] + ks_item_domain).ids
        except Exception as e:
            items = self.ks_dashboard_items_ids.search(
                [['ks_dashboard_ninja_board_id', '=', ks_dashboard_id]] + ks_item_domain).ids
        dashboard_data['ks_dashboard_items_ids'] = items
        return dashboard_data

    @api.model
    def ks_fetch_item(self, item_list, ks_dashboard_id, params={}):
        """
        :rtype: object
        :param item_list: list of item ids.
        :return: {'id':[item_data]}
        """
        self = self.ks_set_date(ks_dashboard_id)
        items = {}
        item_model = self.env['ks_dashboard_ninja.item']
        for item_id in item_list:
            item = self.ks_fetch_item_data(item_model.browse(item_id), params)
            items[item['id']] = item
        return items

    # fetching Item info (Divided to make function inherit easily)
    def ks_fetch_item_data(self, rec, params={}):
        """
        :rtype: object
        :param item_id: item object
        :return: object with formatted item data
        """
        try:
            ks_precision = self.sudo().env.ref('ks_dashboard_ninja.ks_dashboard_ninja_precision')
            ks_precision_digits = ks_precision.digits
            if ks_precision_digits < 0:
                ks_precision_digits = 2
            if ks_precision_digits > 100:
                ks_precision_digits = 2
        except Exception as e:
            ks_precision_digits = 2

        action = {}
        item_domain1 = params.get('ks_domain_1', [])
        item_domain2 = params.get('ks_domain_2', [])

        ks_action_name = []
        if rec.ks_action_lines:
            for res in rec.ks_action_lines:
                my_dict = {}
                my_dict['id'] = res.id
                my_dict['name'] = res.ks_action_item_name
                my_dict['sequence'] = res.sequence
                ks_action_name.append(my_dict)
            ks_action_name.sort(key=lambda r: r['sequence'])

        if rec.ks_actions:
            context = {}
            try:
                context = eval(rec.ks_actions.context)
            except Exception:
                context = {}

                # Managing those views that have the access rights
            ks_actions = rec.ks_actions.sudo()
            action['name'] = ks_actions.name
            action['type'] = ks_actions.type
            action['res_model'] = ks_actions.res_model
            action['views'] = ks_actions.views
            action['view_mode'] = ks_actions.view_mode
            action['search_view_id'] = ks_actions.search_view_id.id
            action['context'] = context
            action['target'] = 'current'
        elif rec.ks_is_client_action and rec.ks_client_action:
            clint_action = {}
            try:
                context = eval(rec.ks_client_action.context)
            except Exception:
                context = {}
            ks_client_action = rec.ks_client_action.sudo()
            clint_action['name'] = ks_client_action.name
            clint_action['type'] = ks_client_action.type
            clint_action['res_model'] = ks_client_action.res_model
            clint_action['xml_id'] = ks_client_action.xml_id
            clint_action['tag'] = ks_client_action.tag
            clint_action['binding_type'] = ks_client_action.binding_type
            clint_action['params'] = ks_client_action.params
            clint_action['target'] = 'current'
            clint_action['context'] = context,
            clint_action['report_id'] = context.get('report_id', False)
            clint_action['resId'] = ks_client_action.id
            context.update({
                'resId': ks_client_action.id
            })

            clint_action['params'] = {
                'options': context,
                'props': {'resId': ks_client_action.id}
            }


            action = clint_action,
        else:
            action = False
        ks_currency_symbol = False
        ks_currency_position = False
        if rec.ks_unit and rec.ks_unit_selection == 'monetary':
            try:
                ks_currency_symbol = self.env.user.company_id.currency_id.symbol
                ks_currency_position = self.env.user.company_id.currency_id.position
            except Exception as E:
                ks_currency_symbol = False
                ks_currency_position = False

        item = {
            'name': rec.name if rec.name else rec.ks_model_id.name if rec.ks_model_id else "Name",
            'ks_background_color': rec.ks_background_color,
            'ks_font_color': rec.ks_font_color,
            'ks_header_bg_color': rec.ks_header_bg_color,
            # 'ks_domain': rec.ks_domain.replace('"%UID"', str(
            #     self.env.user.id)) if rec.ks_domain and "%UID" in rec.ks_domain else rec.ks_domain,
            'ks_domain': rec.ks_convert_into_proper_domain(rec.ks_domain, rec, item_domain1),
            'ks_dashboard_id': rec.ks_dashboard_ninja_board_id.id,
            'ks_icon': rec.ks_icon,
            'ks_model_id': rec.ks_model_id.id,
            'ks_model_name': rec.ks_model_name,
            'ks_model_display_name': rec.ks_model_id.name,
            'ks_record_count_type': rec.ks_record_count_type,
            'ks_record_count': rec._ksGetRecordCount(item_domain1),
            'id': rec.id,
            'ks_layout': rec.ks_layout,
            'ks_icon_select': rec.ks_icon_select,
            'ks_default_icon': rec.ks_default_icon,
            'ks_default_icon_color': rec.ks_default_icon_color,
            # Pro Fields
            'ks_dashboard_item_type': rec.ks_dashboard_item_type,
            'ks_chart_item_color': rec.ks_chart_item_color,
            'ks_chart_groupby_type': rec.ks_chart_groupby_type,
            'ks_chart_measure_field': rec.ks_chart_measure_field.ids,
            'ks_chart_measure_field_2': rec.ks_chart_measure_field_2.ids,
            'ks_chart_relation_groupby': rec.ks_chart_relation_groupby.id,
            'ks_chart_relation_groupby_name': rec.ks_chart_relation_groupby.name,
            'ks_chart_date_groupby': rec.ks_chart_date_groupby,
            'ks_chart_sub_groupby_type': rec.ks_chart_sub_groupby_type,
            'ks_chart_relation_sub_groupby': rec.ks_chart_relation_sub_groupby.id,
            'ks_chart_relation_sub_groupby_name': rec.ks_chart_relation_sub_groupby.name,
            'ks_chart_date_sub_groupby': rec.ks_chart_date_sub_groupby,
            'ks_record_field': rec.ks_record_field.id if rec.ks_record_field else False,
            'ks_chart_data': rec._ks_get_chart_data(item_domain1),
            'ks_list_view_data': rec._ksGetListViewData(item_domain1),
            'ks_chart_data_count_type': rec.ks_chart_data_count_type,
            'ks_bar_chart_stacked': rec.ks_bar_chart_stacked,
            'ks_semi_circle_chart': rec.ks_semi_circle_chart,
            'ks_list_view_type': rec.ks_list_view_type,
            'ks_list_view_group_fields': rec.ks_list_view_group_fields.ids if rec.ks_list_view_group_fields else False,
            'ks_previous_period': rec.ks_previous_period,
            'ks_kpi_data': rec._ksGetKpiData(item_domain1, item_domain2),
            'ks_goal_enable': rec.ks_goal_enable,
            'ks_model_id_2': rec.ks_model_id_2.id,
            'ks_record_field_2': rec.ks_record_field_2.id,
            'ks_data_comparison': rec.ks_data_comparison,
            'ks_target_view': rec.ks_target_view,
            'ks_date_filter_selection': rec.ks_date_filter_selection,
            'ks_show_data_value': rec.ks_show_data_value,
            'ks_show_records': rec.ks_show_records,
            'ks_unit': rec.ks_unit,
            'ks_unit_selection': rec.ks_unit_selection,
            'ks_chart_unit': rec.ks_chart_unit,
            # 'action_id': rec.ks_actions.id if rec.ks_actions else False,
            'sequence': 0,
            'max_sequnce': len(rec.ks_action_lines) if rec.ks_action_lines else False,
            'action': action,
            'ks_hide_legend': rec.ks_hide_legend,
            'ks_radial_legend': rec.ks_radial_legend,
            'ks_data_calculation_type': rec.ks_data_calculation_type,
            'ks_export_all_records': rec.ks_export_all_records,
            'ks_data_formatting': rec.ks_data_format,
            'ks_is_client_action': rec.ks_is_client_action,
            'ks_pagination_limit': rec.ks_pagination_limit,
            'ks_record_data_limit': rec.ks_record_data_limit,
            'ks_chart_cumulative_field': rec.ks_chart_cumulative_field.ids,
            'ks_chart_cumulative': rec.ks_chart_cumulative,
            'ks_chart_is_cumulative': rec.ks_chart_is_cumulative,
            'ks_button_color': rec.ks_button_color,
            'ks_to_do_data': rec._ksGetToDOData(),
            'ks_multiplier_active': rec.ks_multiplier_active,
            'ks_multiplier': rec.ks_multiplier,
            'ks_goal_liness': True if rec.ks_goal_lines else False,
            'ks_currency_symbol': ks_currency_symbol,
            'ks_currency_id':self.env.user.company_id.currency_id.id,
            'ks_currency_position': ks_currency_position,
            'ks_precision_digits': ks_precision_digits if ks_precision_digits else 2,
            'ks_data_label_type': rec.ks_data_label_type,
            'ks_as_of_now': rec.ks_as_of_now,
            'ks_info': rec.ks_info,
            'ks_company': rec.ks_company_id.name if rec.ks_company_id else False,
            'ks_scatter_measure_x_id': rec.ks_scatter_measure_x_id,
            # 'ks_scatter_measure_y_id': rec.ks_scatter_measure_y_id,
            'ks_is_scatter_group': rec.ks_is_scatter_group,
            'ks_bounds': rec.ks_bounds,
            'ks_partners_map': rec.ks_partners_map,
            'ks_funnel_record_field':rec.ks_funnel_record_field,
            'ks_map_record_field':rec.ks_map_record_field,
            'ks_country_id':rec.ks_country_id.id,
            'ks_action_name':ks_action_name if ks_action_name else False
            # 'ks_last_index':ks_last_index
            # 'ks_id_name':','.join(ks_id_name)
        }
        return item

    def ks_set_date(self, ks_dashboard_id):
        ks_dashboard_rec = self.browse(ks_dashboard_id)
        if self._context.get('ksDateFilterSelection', False):
            ks_date_filter_selection = self._context['ksDateFilterSelection']
            if ks_date_filter_selection == 'l_custom':
                ks_start_dt_parse = parse(self._context['ksDateFilterStartDate'])
                ks_end_dt_parse = parse(self._context['ksDateFilterEndDate'])
                self = self.with_context(
                    ksDateFilterStartDate=fields.datetime.strptime(ks_start_dt_parse.strftime("%Y-%m-%d %H:%M:%S"),
                                                                   "%Y-%m-%d %H:%M:%S"))
                self = self.with_context(
                    ksDateFilterEndDate=fields.datetime.strptime(ks_end_dt_parse.strftime("%Y-%m-%d %H:%M:%S"),
                                                                 "%Y-%m-%d %H:%M:%S"))
                self = self.with_context(ksIsDefultCustomDateFilter=False)

        else:
            ks_date_filter_selection = ks_dashboard_rec.ks_date_filter_selection
            self = self.with_context(ksDateFilterStartDate=ks_dashboard_rec.ks_dashboard_start_date)
            self = self.with_context(ksDateFilterEndDate=ks_dashboard_rec.ks_dashboard_end_date)
            self = self.with_context(ksDateFilterSelection=ks_date_filter_selection)
            self = self.with_context(ksIsDefultCustomDateFilter=True)

        if ks_date_filter_selection not in ['l_custom', 'l_none']:
            ks_date_data = ks_get_date(ks_date_filter_selection, self, 'datetime')
            self = self.with_context(ksDateFilterStartDate=ks_date_data["selected_start_date"])
            self = self.with_context(ksDateFilterEndDate=ks_date_data["selected_end_date"])

        return self

    @api.model
    def ks_get_list_view_data_offset(self, ks_dashboard_item_id, offset, dashboard_id, params={}):
        item_domain = params.get('ks_domain_1', [])
        self = self.ks_set_date(dashboard_id)
        item = self.ks_dashboard_items_ids.browse(ks_dashboard_item_id)

        return item.ks_get_next_offset(ks_dashboard_item_id, offset, item_domain)

    def ks_view_items_view(self):
        self.ensure_one()
        return {
            'name': _("Dashboard Items"),
            'res_model': 'ks_dashboard_ninja.item',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(False, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('ks_dashboard_ninja_board_id', '!=', False)],
            'search_view_id': self.env.ref('ks_dashboard_ninja.ks_item_search_view').id,
            'context': {
                'search_default_ks_dashboard_ninja_board_id': self.id,
                'group_by': 'ks_dashboard_ninja_board_id',
            },
            'help': _('''<p class="o_view_nocontent_smiling_face">
                                        You can find all items related to Dashboard Here.</p>
                                    '''),

        }

    def ks_export_item(self, item_id):
        return {
            'ks_file_format': 'ks_dashboard_ninja_item_export',
            'item': self.ks_export_item_data(self.ks_dashboard_items_ids.browse(int(item_id)))
        }

    # fetching Item info (Divided to make function inherit easily)
    def ks_export_item_data(self, rec):
        ks_timezone = self._context.get('tz') or self.env.user.tz
        ks_chart_measure_field = []
        ks_chart_measure_field_2 = []
        if rec.ks_many2many_field_ordering:
            ks_many2many_field_ordering = json.loads(rec.ks_many2many_field_ordering)
        else:
            ks_many2many_field_ordering =  {}
        if ks_many2many_field_ordering.get('ks_list_view_fields', False):
            ks_list_view_fields_list = self.env['ir.model.fields'].search([('id', 'in',
                                                    ks_many2many_field_ordering.get('ks_list_view_fields', False))])
        if ks_many2many_field_ordering.get('ks_list_view_group_fields', False):
            ks_list_view_group_fields_list = self.env['ir.model.fields'].search([('id', 'in',
                                           ks_many2many_field_ordering.get('ks_list_view_group_fields', False))])
        if ks_many2many_field_ordering.get('ks_chart_measure_field', False):
            ks_chart_measure_field_list = self.env['ir.model.fields'].search([('id', 'in',
                                   ks_many2many_field_ordering.get('ks_chart_measure_field', False))])
        if ks_many2many_field_ordering.get('ks_chart_measure_field_2', False):
            ks_chart_measure_field_2_list = self.env['ir.model.fields'].search([('id', 'in',
                               ks_many2many_field_ordering.get('ks_chart_measure_field_2', False))])

        try:
            for res in ks_chart_measure_field_list:
                ks_chart_measure_field.append(res.name)
        except Exception as E:
            ks_chart_measure_field = []
        try:
            for res in ks_chart_measure_field_2_list:
                ks_chart_measure_field_2.append(res.name)
        except Exception as E:
            ks_chart_measure_field_2 = []
        ks_multiplier_fields = []
        ks_multiplier_value = []
        if rec.ks_multiplier_lines:
            for ress in rec.ks_multiplier_lines.ks_multiplier_fields:
                ks_multiplier_fields.append(ress.name)
            for ks_val in rec.ks_multiplier_lines:
                ks_multiplier_value.append(ks_val.ks_multiplier_value)

        ks_list_view_group_fields = []
        try:
            for res in ks_list_view_group_fields_list:
                ks_list_view_group_fields.append(res.name)
        except Exception as e:
            ks_list_view_group_fields = []
        ks_goal_lines = []
        for res in rec.ks_goal_lines:
            goal_line = {
                'ks_goal_date': datetime.datetime.strftime(res.ks_goal_date, "%Y-%m-%d"),
                'ks_goal_value': res.ks_goal_value,
            }
            ks_goal_lines.append(goal_line)
        ks_dn_header_lines = []
        for res in rec.ks_dn_header_lines:
            ks_dn_header_line = {
                'ks_to_do_header': res.ks_to_do_header
            }

            if res.ks_to_do_description_lines:
                ks_to_do_description_lines = []
                for ks_description_line in res.ks_to_do_description_lines:
                    description_line = {
                        'ks_description': ks_description_line.ks_description,
                        'ks_active': ks_description_line.ks_active,
                    }
                    ks_to_do_description_lines.append(description_line)
                ks_dn_header_line[res.ks_to_do_header] = ks_to_do_description_lines
            ks_dn_header_lines.append(ks_dn_header_line)

        ks_action_lines = []
        for res in rec.ks_action_lines:
            action_line = {
                'ks_item_action_field': res.ks_item_action_field.name,
                'ks_item_action_date_groupby': res.ks_item_action_date_groupby,
                'ks_chart_type': res.ks_chart_type,
                'ks_sort_by_field': res.ks_sort_by_field.name,
                'ks_sort_by_order': res.ks_sort_by_order,
                'ks_record_limit': res.ks_record_limit,
                'sequence': res.sequence,
                'ks_action_item_name': res.ks_action_item_name
            }
            ks_action_lines.append(action_line)
        ks_multiplier_lines = []
        for res in rec.ks_multiplier_lines:
            ks_multiplier_line = {
                'ks_multiplier_fields': res.ks_multiplier_fields.id,
                'ks_multiplier_value': res.ks_multiplier_value,
                'ks_dashboard_item_id': rec.id,
                'ks_model_id': rec.ks_model_id.id
            }
            ks_multiplier_lines.append(ks_multiplier_line)

        ks_list_view_field = []
        try:
            for res in ks_list_view_fields_list:
                ks_list_view_field.append(res.name)
        except Exception as e:
            ks_list_view_field = []
        val = str(rec.id)
        keys_data = {}
        selecred_rec = self.env['ks_dashboard_ninja.child_board'].search(
            [['id', 'in', rec.ks_dashboard_ninja_board_id.ks_child_dashboard_ids.ids], ['ks_active', '=', True],
             ['company_id', '=', self.env.company.id]], limit=1)
        if rec.ks_dashboard_ninja_board_id.ks_gridstack_config:
            keys_data = json.loads(rec.ks_dashboard_ninja_board_id.ks_gridstack_config)
        elif selecred_rec:
            keys_data = json.loads(selecred_rec.ks_gridstack_config)
        elif rec.ks_dashboard_ninja_board_id.ks_child_dashboard_ids[0].ks_gridstack_config:
            keys_data = json.loads(rec.ks_dashboard_ninja_board_id.ks_child_dashboard_ids[0].ks_gridstack_config)
        elif self._context.get('gridstack_config', False):
            keys_data = self._context.get('gridstack_config', False)
        else:
            if rec.grid_corners:
                keys_data = {rec.id: json.loads(rec.grid_corners.replace("\'", "\""))}
        keys_list = keys_data.keys()
        grid_corners = {}
        if val in keys_list:
            grid_corners = keys_data.get(str(val))

        item = {
            'name': rec.name if rec.name else rec.ks_model_id.name if rec.ks_model_id else "Name",
            'ks_background_color': rec.ks_background_color,
            'ks_font_color': rec.ks_font_color,
            'ks_header_bg_color': rec.ks_header_bg_color,
            'ks_domain': rec.ks_domain,
            'ks_icon': str(rec.ks_icon) if rec.ks_icon else False,
            'ks_id': rec.id,
            'ks_model_id': rec.ks_model_name,
            'ks_record_count': rec.ks_record_count,
            'ks_layout': rec.ks_layout,
            'ks_icon_select': rec.ks_icon_select,
            'ks_default_icon': rec.ks_default_icon,
            'ks_default_icon_color': rec.ks_default_icon_color,
            'ks_record_count_type': rec.ks_record_count_type,
            # Pro Fields
            'ks_dashboard_item_type': rec.ks_dashboard_item_type,
            'ks_chart_item_color': rec.ks_chart_item_color,
            'ks_chart_groupby_type': rec.ks_chart_groupby_type,
            'ks_chart_relation_groupby': rec.ks_chart_relation_groupby.name,
            'ks_chart_date_groupby': rec.ks_chart_date_groupby,
            'ks_record_field': rec.ks_record_field.name,
            'ks_chart_sub_groupby_type': rec.ks_chart_sub_groupby_type,
            'ks_chart_relation_sub_groupby': rec.ks_chart_relation_sub_groupby.name,
            'ks_chart_date_sub_groupby': rec.ks_chart_date_sub_groupby,
            'ks_chart_data_count_type': rec.ks_chart_data_count_type,
            'ks_chart_measure_field': ks_chart_measure_field,
            'ks_chart_measure_field_2': ks_chart_measure_field_2,
            'ks_list_view_fields': ks_list_view_field,
            'ks_list_view_group_fields': ks_list_view_group_fields,
            'ks_list_view_type': rec.ks_list_view_type,
            'ks_record_data_limit': rec.ks_record_data_limit,
            'ks_sort_by_order': rec.ks_sort_by_order,
            'ks_sort_by_field': rec.ks_sort_by_field.name,
            'ks_date_filter_field': rec.ks_date_filter_field.name,
            'ks_goal_enable': rec.ks_goal_enable,
            'ks_standard_goal_value': rec.ks_standard_goal_value,
            'ks_goal_liness': ks_goal_lines,
            'ks_date_filter_selection': rec.ks_date_filter_selection,
            'ks_item_start_date': rec.ks_item_start_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if rec.ks_item_start_date else False,
            'ks_item_end_date': rec.ks_item_end_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if rec.ks_item_end_date else False,
            'ks_date_filter_selection_2': rec.ks_date_filter_selection_2,
            'ks_item_start_date_2': rec.ks_item_start_date_2.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if rec.ks_item_start_date_2 else False,
            'ks_item_end_date_2': rec.ks_item_end_date_2.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if rec.ks_item_end_date_2 else False,
            'ks_previous_period': rec.ks_previous_period,
            'ks_target_view': rec.ks_target_view,
            'ks_data_comparison': rec.ks_data_comparison,
            'ks_record_count_type_2': rec.ks_record_count_type_2,
            'ks_record_field_2': rec.ks_record_field_2.name,
            'ks_model_id_2': rec.ks_model_id_2.model,
            'ks_date_filter_field_2': rec.ks_date_filter_field_2.name,
            'ks_action_liness': ks_action_lines,
            'ks_compare_period': rec.ks_compare_period,
            'ks_year_period': rec.ks_year_period,
            'ks_compare_period_2': rec.ks_compare_period_2,
            'ks_year_period_2': rec.ks_year_period_2,
            'ks_domain_2': rec.ks_domain_2,
            'ks_show_data_value': rec.ks_show_data_value,
            'ks_list_target_deviation_field': rec.ks_list_target_deviation_field.name,
            'ks_unit': rec.ks_unit,
            'ks_show_records': rec.ks_show_records,
            'ks_hide_legend': rec.ks_hide_legend,
            'ks_radial_legend': rec.ks_radial_legend,
            'ks_fill_temporal': rec.ks_fill_temporal,
            'ks_domain_extension': rec.ks_domain_extension,
            'ks_unit_selection': rec.ks_unit_selection,
            'ks_chart_unit': rec.ks_chart_unit,
            'ks_bar_chart_stacked': rec.ks_bar_chart_stacked,
            'ks_goal_bar_line': rec.ks_goal_bar_line,
            'ks_actions': rec.ks_actions.xml_id if rec.ks_actions else False,
            'ks_client_action': rec.ks_client_action.xml_id if rec.ks_client_action else False,
            'ks_is_client_action': rec.ks_is_client_action,
            'ks_export_all_records': rec.ks_export_all_records,
            'ks_record_data_limit_visibility': rec.ks_record_data_limit_visibility,
            'ks_data_format': rec.ks_data_format,
            'ks_pagination_limit': rec.ks_pagination_limit,
            'ks_chart_cumulative_field': rec.ks_chart_cumulative_field.ids,
            'ks_chart_cumulative': rec.ks_chart_cumulative,
            'ks_button_color': rec.ks_button_color,
            'ks_dn_header_line': ks_dn_header_lines,
            'ks_semi_circle_chart': rec.ks_semi_circle_chart,
            'ks_multiplier_active': rec.ks_multiplier_active,
            'ks_multiplier': rec.ks_multiplier,
            'ks_multiplier_lines': ks_multiplier_lines if ks_multiplier_lines else False,
            'ks_many2many_field_ordering': rec.ks_many2many_field_ordering,
            'ks_data_label_type': rec.ks_data_label_type,
            'ks_as_of_now': rec.ks_as_of_now,
            'ks_scatter_measure_x_id': rec.ks_chart_relation_groupby.name,
            # 'ks_scatter_measure_y_id': ks_chart_measure_field,
            'ks_is_scatter_group': rec.ks_is_scatter_group,
            'ks_country_id': rec.ks_country_id.id,
            'ks_bounds': rec.ks_bounds,
            'ks_partners_map': rec.ks_partners_map,

        }
        if grid_corners:
            item.update({
                'grid_corners': grid_corners,
            })
        return item

    def ks_open_import(self, **kwargs):
        action = self.env['ir.actions.act_window']._for_xml_id('ks_dashboard_ninja.ks_import_dashboard_action')
        return action

    def ks_open_setting(self, **kwargs):
        action = self.env['ir.actions.act_window']._for_xml_id('ks_dashboard_ninja.board_form_tree_action_window')
        # action['res_id'] = self.id
        # action['target'] = 'new'
        # action['context'] = {'form_view_ref':'ks_dashboard_ninja.board_form'}
        # action['view_mode']='form'
        return action

    def ks_delete_dashboard(self):
        if str(self.id) in self.ks_dashboard_default_template:
            raise ValidationError(_('You cannot delete any default template'))
        else:
            self.search([('id', '=', self.id)]).unlink()
            return {
                'type': 'ir.actions.client',
                'name': "Dashboard Ninja",
                'res_model': 'ks_dashboard_ninja.board',
                'params': {'ks_dashboard_id': 1},
                'tag': 'ks_dashboard_ninja',
            }

    def ks_create_dashboard(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ks_dashboard_ninja.board_form_tree_action_window')
        action['target'] = 'new'
        return action

    def ks_import_item(self, dashboard_id, **kwargs):
        try:
            # ks_dashboard_data = json.loads(file)
            file = kwargs.get('file', False)
            ks_dashboard_file_read = json.loads(file)
        except Exception:
            raise ValidationError(_("This file is not supported"))

        if 'ks_file_format' in ks_dashboard_file_read and ks_dashboard_file_read[
            'ks_file_format'] == 'ks_dashboard_ninja_item_export':
            item = ks_dashboard_file_read['item']
        else:
            raise ValidationError(_("Current Json File is not properly formatted according to Dashboard Ninja Model."))

        item['ks_dashboard_ninja_board_id'] = int(dashboard_id)
        item['ks_company_id'] = False
        self.ks_create_item(item)

        return "Success"

    @api.model
    def ks_dashboard_export(self, ks_dashboard_ids, **kwargs):
        ks_dashboard_data = []
        ks_dashboard_export_data = {}
        if kwargs.get('dashboard_id'):
            ks_dashboard_ids = '['+str(ks_dashboard_ids)+']'
        ks_dashboard_ids = json.loads(ks_dashboard_ids)
        for ks_dashboard_id in ks_dashboard_ids:
            dash = self.search([('id', '=', ks_dashboard_id)])
            selecred_rec = self.env['ks_dashboard_ninja.child_board'].search(
                [['id', 'in', dash.ks_child_dashboard_ids.ids], ['ks_active', '=', True],
                 ['company_id', '=', self.env.company.id]], limit=1)
            ks_dashboard_rec = self.browse(ks_dashboard_id)
            if selecred_rec:
                name = selecred_rec.name
                grid_conf = selecred_rec.ks_gridstack_config
            elif dash.ks_child_dashboard_ids:
                name = dash.display_name
                grid_conf = dash.ks_child_dashboard_ids[0].ks_gridstack_config
            else:
                name = dash.name
                grid_conf = dash.ks_gridstack_config
            dashboard_data = self.ks_prepare_export_data_vals(ks_dashboard_rec, grid_conf=grid_conf)
            if selecred_rec:
                dashboard_data['name'] = selecred_rec.name
                dashboard_data['ks_gridstack_config'] = selecred_rec.ks_gridstack_config
            elif len(ks_dashboard_rec.ks_child_dashboard_ids) > 1:
                dashboard_data['name'] = ks_dashboard_rec.ks_child_dashboard_ids[0].name
                dashboard_data['ks_gridstack_config'] = ks_dashboard_rec.ks_child_dashboard_ids[0].ks_gridstack_config
            if dashboard_data['name'] == 'Default Board Layout':
                dashboard_data['name'] = ks_dashboard_rec.ks_dashboard_menu_name
            if len(ks_dashboard_rec.ks_dashboard_items_ids) < 1:
                dashboard_data['ks_item_data'] = False
            else:
                items = []
                for rec in ks_dashboard_rec.ks_dashboard_items_ids:
                    item = self.ks_export_item_data(rec)
                    items.append(item)

                dashboard_data['ks_item_data'] = items
            ks_dashboard_data.append(dashboard_data)

            ks_dashboard_export_data = {
                'ks_file_format': 'ks_dashboard_ninja_export_file',
                'ks_dashboard_data': ks_dashboard_data
            }
        return ks_dashboard_export_data

    def ks_prepare_export_data_vals(self, ks_dashboard_rec, grid_conf=None,):
        dashboard_data = {
            'name': ks_dashboard_rec.name,
            'ks_dashboard_menu_name': ks_dashboard_rec.ks_dashboard_menu_name,
            'ks_gridstack_config': grid_conf if grid_conf else '{}',
            'ks_set_interval': ks_dashboard_rec.ks_set_interval,
            'ks_date_filter_selection': ks_dashboard_rec.ks_date_filter_selection,
            'ks_dashboard_start_date': ks_dashboard_rec.ks_dashboard_start_date,
            'ks_dashboard_end_date': ks_dashboard_rec.ks_dashboard_end_date,
            'ks_dashboard_top_menu_id': ks_dashboard_rec.ks_dashboard_top_menu_id.id,
            'ks_data_formatting': ks_dashboard_rec.ks_data_formatting,
        }
        return dashboard_data

    @api.model
    def ks_import_dashboard(self, file, menu_id):
        try:
            # ks_dashboard_data = json.loads(file)
            ks_dashboard_file_read = json.loads(file)
        except Exception:
            raise ValidationError(_("This file is not supported"))

        if 'ks_file_format' in ks_dashboard_file_read and ks_dashboard_file_read[
            'ks_file_format'] == 'ks_dashboard_ninja_export_file':
            ks_dashboard_data = ks_dashboard_file_read['ks_dashboard_data']
            for i in range(len(ks_dashboard_data)):
                if 'ks_set_interval' in ks_dashboard_data[i].keys() and ks_dashboard_data[i].get('ks_item_data', False):
                    # del ks_dashboard_data[i]['ks_set_interval']
                    for j in range(len(ks_dashboard_data[i].get('ks_item_data', False))):
                        if 'ks_update_items_data' in ks_dashboard_data[i].get('ks_item_data', False)[j].keys():
                            del ks_dashboard_data[i].get('ks_item_data', False)[j]['ks_update_items_data']
                        if 'ks_auto_update_type' in ks_dashboard_data[i].get('ks_item_data', False)[j].keys():
                            del ks_dashboard_data[i].get('ks_item_data', False)[j]['ks_auto_update_type']
                        if 'ks_show_live_pop_up' in ks_dashboard_data[i].get('ks_item_data', False)[j].keys():
                            del ks_dashboard_data[i].get('ks_item_data', False)[j]['ks_show_live_pop_up']
        else:
            raise ValidationError(_("Current Json File is not properly formatted according to Dashboard Ninja Model."))

        ks_dashboard_key = ['name', 'ks_dashboard_menu_name', 'ks_gridstack_config']
        ks_dashboard_item_key = ['ks_model_id', 'ks_chart_measure_field', 'ks_list_view_fields', 'ks_record_field',
                                 'ks_chart_relation_groupby', 'ks_id']

        # Fetching dashboard model info
        for data in ks_dashboard_data:
            if not all(key in data for key in ks_dashboard_key):
                raise ValidationError(
                    _("Current Json File is not properly formatted according to Dashboard Ninja Model."))
            ks_dashboard_top_menu_id = data.get('ks_dashboard_top_menu_id', False)
            if ks_dashboard_top_menu_id:
                try:
                    self.env['ir.ui.menu'].browse(ks_dashboard_top_menu_id).name
                    ks_dashboard_top_menu_id = self.env['ir.ui.menu'].browse(ks_dashboard_top_menu_id)
                except Exception:
                    ks_dashboard_top_menu_id = False
            vals = self.ks_prepare_import_data_vals(data, menu_id)
            # Creating Dashboard
            dashboard_id = self.create(vals)

            if data['ks_gridstack_config']:
                ks_gridstack_config = eval(data['ks_gridstack_config'])
            ks_grid_stack_config = {}

            item_ids = []
            item_new_ids = []
            ks_skiped = False
            if data['ks_item_data']:
                # Fetching dashboard item info
                ks_skiped = 0
                for item in data['ks_item_data']:
                    item['ks_company_id'] = False
                    if not all(key in item for key in ks_dashboard_item_key):
                        raise ValidationError(
                            _("Current Json File is not properly formatted according to Dashboard Ninja Model."))

                    # Creating dashboard items
                    item['ks_dashboard_ninja_board_id'] = dashboard_id.id
                    item_ids.append(item['ks_id'])
                    del item['ks_id']

                    if 'ks_data_calculation_type' in item:
                        if item['ks_data_calculation_type'] == 'custom':
                            del item['ks_data_calculation_type']
                            del item['ks_custom_query']
                            del item['ks_xlabels']
                            del item['ks_ylabels']
                            del item['ks_list_view_layout']
                            ks_item = self.ks_create_item(item)
                            item_new_ids.append(ks_item.id)
                        else:
                            ks_skiped += 1
                    else:
                        ks_item = self.ks_create_item(item)
                        item_new_ids.append(ks_item.id)

            for id_index, id in enumerate(item_ids):
                if data['ks_gridstack_config'] and str(id) in ks_gridstack_config:
                    ks_grid_stack_config[str(item_new_ids[id_index])] = ks_gridstack_config[str(id)]
                    # if id_index in item_new_ids:

            self.browse(dashboard_id.id).write({
                'ks_gridstack_config': json.dumps(ks_grid_stack_config)
            })

            if ks_skiped:
                return {
                    'ks_skiped_items': ks_skiped,
                }

        return "Success"
        # separate function to make item for import

    def ks_prepare_import_data_vals(self, data, menu_id):
        vals = {
            'name': data['name'],
            'ks_dashboard_menu_name': data['ks_dashboard_menu_name'],
            'ks_dashboard_top_menu_id': menu_id.id if menu_id else self.env.ref(
                "ks_dashboard_ninja.board_menu_root").id,
            'ks_dashboard_active': True,
            'ks_gridstack_config': data['ks_gridstack_config'],
            'ks_dashboard_default_template': self.env.ref("ks_dashboard_ninja.ks_blank").id,
            'ks_dashboard_group_access': False,
            'ks_set_interval': data['ks_set_interval'],
            'ks_date_filter_selection': data['ks_date_filter_selection'],
            'ks_dashboard_start_date': data['ks_dashboard_start_date'],
            'ks_dashboard_end_date': data['ks_dashboard_end_date'],
        }
        return vals

    def ks_create_item(self, item):
        model = self.env['ir.model'].search([('model', '=', item['ks_model_id'])])

        if not model and not item['ks_dashboard_item_type'] == 'ks_to_do':
            raise ValidationError(_(
                "Please Install the Module which contains the following Model : %s " % item['ks_model_id']))

        ks_model_name = item['ks_model_id']

        ks_goal_lines = item['ks_goal_liness'].copy() if item.get('ks_goal_liness', False) else False
        ks_action_lines = item['ks_action_liness'].copy() if item.get('ks_action_liness', False) else False
        ks_multiplier_lines = item['ks_multiplier_lines'].copy() if item.get('ks_multiplier_lines', False) else False
        ks_dn_header_line = item['ks_dn_header_line'].copy() if item.get('ks_dn_header_line', False) else False

        # Creating dashboard items
        item = self.ks_prepare_item(item)

        if 'ks_goal_liness' in item:
            del item['ks_goal_liness']
        if 'ks_id' in item:
            del item['ks_id']
        if 'ks_action_liness' in item:
            del item['ks_action_liness']
        if 'ks_icon' in item:
            item['ks_icon_select'] = "Default"
            item['ks_icon'] = False
        if 'ks_dn_header_line' in item:
            del item['ks_dn_header_line']
        if 'ks_multiplier_lines' in item:
            del item['ks_multiplier_lines']

        ks_item = self.env['ks_dashboard_ninja.item'].create(item)

        if ks_goal_lines and len(ks_goal_lines) != 0:
            for line in ks_goal_lines:
                line['ks_goal_date'] = datetime.datetime.strptime(line['ks_goal_date'].split(" ")[0],
                                                                  '%Y-%m-%d')
                line['ks_dashboard_item'] = ks_item.id
                self.env['ks_dashboard_ninja.item_goal'].create(line)

        if ks_dn_header_line and len(ks_dn_header_line) != 0:
            for line in ks_dn_header_line:
                ks_line = {}
                ks_line['ks_to_do_header'] = line.get('ks_to_do_header')
                ks_line['ks_dn_item_id'] = ks_item.id
                ks_dn_header_id = self.env['ks_to.do.headers'].create(ks_line)
                if line.get(line.get('ks_to_do_header'), False):
                    for ks_task in line.get(line.get('ks_to_do_header')):
                        ks_task['ks_to_do_header_id'] = ks_dn_header_id.id
                        self.env['ks_to.do.description'].create(ks_task)

        if ks_action_lines and len(ks_action_lines) != 0:

            for line in ks_action_lines:
                if line['ks_sort_by_field']:
                    ks_sort_by_field = line['ks_sort_by_field']
                    ks_sort_record_id = self.env['ir.model.fields'].search(
                        [('model', '=', ks_model_name), ('name', '=', ks_sort_by_field)])
                    if ks_sort_record_id:
                        line['ks_sort_by_field'] = ks_sort_record_id.id
                    else:
                        line['ks_sort_by_field'] = False
                if line['ks_item_action_field']:
                    ks_item_action_field = line['ks_item_action_field']
                    ks_record_id = self.env['ir.model.fields'].search(
                        [('model', '=', ks_model_name), ('name', '=', ks_item_action_field)])
                    if ks_record_id:
                        line['ks_item_action_field'] = ks_record_id.id
                        line['ks_dashboard_item_id'] = ks_item.id
                        self.env['ks_dashboard_ninja.item_action'].create(line)

        if ks_multiplier_lines and len(ks_multiplier_lines) != 0:
            for rec in ks_multiplier_lines:
                ks_multiplier_field = rec['ks_multiplier_fields']
                ks_multiplier_field_id = self.env['ir.model.fields'].search(
                    [('model', '=', ks_model_name), ('id', '=', ks_multiplier_field)])
                if ks_multiplier_field:
                    rec['ks_multiplier_fields'] = ks_multiplier_field_id.id
                    rec['ks_dashboard_item_id'] = ks_item.id
                    self.env['ks_dashboard_item.multiplier'].create(rec)

        return ks_item

    def ks_prepare_item(self, item):
        try:
            ks_measure_field_ids = []
            ks_measure_field_2_ids = []
            ks_many2many_field_ordering = item['ks_many2many_field_ordering'] if item.get('ks_many2many_field_ordering', False) else False
            ks_list_view_group_fields_name = False
            ks_list_view_fields_name = False
            ks_chart_measure_field_name = False
            ks_chart_measure_field_2_name = False
            if ks_many2many_field_ordering:
                ks_many2many_field_ordering = json.loads(ks_many2many_field_ordering)
                ks_list_view_group_fields_name = ks_many2many_field_ordering.get('ks_list_view_group_fields_name', False)
                ks_list_view_fields_name = ks_many2many_field_ordering.get('ks_list_view_fields_name', False)
                ks_chart_measure_field_name = ks_many2many_field_ordering.get('ks_chart_measure_field_name', False)
                ks_chart_measure_field_2_name = ks_many2many_field_ordering.get('ks_chart_measure_field_2_name', False)
            ks_chart_measure_field = item['ks_chart_measure_field']
            if ks_chart_measure_field_name and len(ks_chart_measure_field_name)>0:
                ks_chart_measure_field = ks_chart_measure_field_name
            for ks_measure in ks_chart_measure_field:
                ks_measure_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_measure), ('model', '=', item['ks_model_id'])])
                if ks_measure_id:
                    ks_measure_field_ids.append(ks_measure_id.id)
            item['ks_chart_measure_field'] = [(6, 0, ks_measure_field_ids)]
            ks_chart_measure_field_2 = item['ks_chart_measure_field_2']
            if ks_chart_measure_field_name and len(ks_chart_measure_field_name) > 0:
                ks_chart_measure_field_2 = ks_chart_measure_field_2_name
            for ks_measure in ks_chart_measure_field_2:
                ks_measure_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_measure), ('model', '=', item['ks_model_id'])])
                if ks_measure_id:
                    ks_measure_field_2_ids.append(ks_measure_id.id)
            item['ks_chart_measure_field_2'] = [(6, 0, ks_measure_field_2_ids)]

            ks_list_view_group_fields_ids = []
            ks_list_view_group_fields = item['ks_list_view_group_fields']
            if ks_list_view_group_fields_name and len(ks_list_view_group_fields_name) > 0:
                ks_list_view_group_fields = ks_list_view_group_fields_name
            for ks_measure in ks_list_view_group_fields:
                ks_measure_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_measure), ('model', '=', item['ks_model_id'])])

                if ks_measure_id:
                    ks_list_view_group_fields_ids.append(ks_measure_id.id)
            item['ks_list_view_group_fields'] = [(6, 0, ks_list_view_group_fields_ids)]

            ks_list_view_field_ids = []

            ks_list_view_fields = item['ks_list_view_fields']
            if ks_list_view_fields_name and len(ks_list_view_fields_name) > 0:
                ks_list_view_fields = ks_list_view_group_fields_name
            for ks_list_field in ks_list_view_fields:
                ks_list_field_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_list_field), ('model', '=', item['ks_model_id'])])
                if ks_list_field_id:
                    ks_list_view_field_ids.append(ks_list_field_id.id)
            item['ks_list_view_fields'] = [(6, 0, ks_list_view_field_ids)]

            if item['ks_record_field']:
                ks_record_field = item['ks_record_field']
                ks_record_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_record_field), ('model', '=', item['ks_model_id'])])
                if ks_record_id:
                    item['ks_record_field'] = ks_record_id.id
                else:
                    item['ks_record_field'] = False

            if item['ks_date_filter_field']:
                ks_date_filter_field = item['ks_date_filter_field']
                ks_record_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_date_filter_field), ('model', '=', item['ks_model_id'])])
                if ks_record_id:
                    item['ks_date_filter_field'] = ks_record_id.id
                else:
                    item['ks_date_filter_field'] = False

            if item['ks_chart_relation_groupby']:
                ks_group_by = item['ks_chart_relation_groupby']
                ks_record_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_group_by), ('model', '=', item['ks_model_id'])])
                if ks_record_id:
                    item['ks_chart_relation_groupby'] = ks_record_id.id
                else:
                    item['ks_chart_relation_groupby'] = False

            if item['ks_chart_relation_sub_groupby']:
                ks_group_by = item['ks_chart_relation_sub_groupby']
                ks_chart_relation_sub_groupby = self.env['ir.model.fields'].search(
                    [('name', '=', ks_group_by), ('model', '=', item['ks_model_id'])])
                if ks_chart_relation_sub_groupby:
                    item['ks_chart_relation_sub_groupby'] = ks_chart_relation_sub_groupby.id
                else:
                    item['ks_chart_relation_sub_groupby'] = False

            if item['ks_dashboard_item_type'] == "ks_scatter_chart" and item[
                'ks_scatter_measure_x_id']:
                # ks_scatter_id = self.env['ir.model.fields'].search(
                #     [('name', '=', item['ks_scatter_measure_y_id'][0]), ('model', '=', item['ks_model_id'])])
                # if ks_scatter_id:
                #     item['ks_scatter_measure_y_id'] = ks_scatter_id.id
                ks_scatter_group_by = item['ks_scatter_measure_x_id']
                ks_record_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_scatter_group_by), ('model', '=', item['ks_model_id'])])
                if ks_record_id:
                    item['ks_scatter_measure_x_id'] = ks_record_id.id
                else:
                    item['ks_scatter_measure_x_id'] = False
            if item["ks_dashboard_item_type"] != "ks_scatter_chart":
                item['ks_scatter_measure_x_id'] = False
                # item['ks_scatter_measure_y_id'] = False

            # Sort by field : Many2one Entery
            if item['ks_sort_by_field']:
                ks_group_by = item['ks_sort_by_field']
                ks_sort_by_field = self.env['ir.model.fields'].search(
                    [('name', '=', ks_group_by), ('model', '=', item['ks_model_id'])])
                if ks_sort_by_field:
                    item['ks_sort_by_field'] = ks_sort_by_field.id
                else:
                    item['ks_sort_by_field'] = False

            if item['ks_list_target_deviation_field']:
                ks_list_target_deviation_field = item['ks_list_target_deviation_field']
                record_id = self.env['ir.model.fields'].search(
                    [('name', '=', ks_list_target_deviation_field), ('model', '=', item['ks_model_id'])])
                if record_id:
                    item['ks_list_target_deviation_field'] = record_id.id
                else:
                    item['ks_list_target_deviation_field'] = False

            ks_model_id = self.env['ir.model'].search([('model', '=', item['ks_model_id'])]).id

            if item.get("ks_actions"):
                ks_action = self.env.ref(item["ks_actions"], False)
                if ks_action:
                    item["ks_actions"] = ks_action.id
                else:
                    item["ks_actions"] = False
            if item.get("ks_client_action"):
                ks_action = self.env.ref(item["ks_client_action"], False)
                if ks_action:
                    item["ks_client_action"] = ks_action.id
                else:
                    item["ks_client_action"] = False

            if (item['ks_model_id_2']):
                ks_model_2 = item['ks_model_id_2'].replace(".", "_")
                ks_model_id_2 = self.env['ir.model'].search([('model', '=', item['ks_model_id_2'])]).id
                if item['ks_record_field_2']:
                    ks_record_field = item['ks_record_field_2']
                    ks_record_id = self.env['ir.model.fields'].search(
                        [('model', '=', item['ks_model_id_2']), ('name', '=', ks_record_field)])

                    if ks_record_id:
                        item['ks_record_field_2'] = ks_record_id.id
                    else:
                        item['ks_record_field_2'] = False
                if item['ks_date_filter_field_2']:
                    ks_record_id = self.env['ir.model.fields'].search(
                        [('model', '=', item['ks_model_id_2']), ('name', '=', item['ks_date_filter_field_2'])])

                    if ks_record_id:
                        item['ks_date_filter_field_2'] = ks_record_id.id
                    else:
                        item['ks_date_filter_field_2'] = False

                item['ks_model_id_2'] = ks_model_id_2
            else:
                item['ks_date_filter_field_2'] = False
                item['ks_record_field_2'] = False

            item['ks_model_id'] = ks_model_id

            item['ks_goal_liness'] = False
            item['ks_item_start_date'] = item['ks_item_start_date'] if \
                item['ks_item_start_date'] else False
            item['ks_item_end_date'] = item['ks_item_end_date'] if \
                item['ks_item_end_date'] else False
            item['ks_item_start_date_2'] = item['ks_item_start_date_2'] if \
                item['ks_item_start_date_2'] else False
            item['ks_item_end_date_2'] = item['ks_item_end_date_2'] if \
                item['ks_item_end_date_2'] else False

            return item
        except Exception as e:
            raise ValidationError('JSON file not supported.')
    @api.model
    def update_child_board(self, action, dashboard_id, data):
        dashboard_id = self.browse(dashboard_id)
        selecred_rec = self.env['ks_dashboard_ninja.child_board'].search(
            [['id', 'in', dashboard_id.ks_child_dashboard_ids.ids],
             ['company_id', '=', self.env.company.id], ['ks_active', '=', True]], limit=1)
        if action == 'create':
            dashboard_id.ks_child_dashboard_ids.write({'ks_active': False})
            result = self.env['ks_dashboard_ninja.child_board'].create(data)
            result = result.id
        elif action == 'update':
            # result = dashboard_id.ks_child_dashboard_ids.search([['ks_active', '=', True]]).write({'ks_active': False})
            if data['ks_selected_board_id'] != 'ks_default':
                selecred_rec.ks_active = False
                result = dashboard_id.ks_child_dashboard_ids.browse(int(data['ks_selected_board_id'])).write(
                    {'ks_active': True})
            else:
                result = dashboard_id.ks_child_dashboard_ids.search([['ks_active', '=', True]]).write(
                    {'ks_active': False})
                for i in dashboard_id.ks_child_dashboard_ids:
                    if i.name == 'Default Board Layout':
                        i.ks_active = True
        return result

    def ks_prepare_dashboard_domain(self):
        pre_defined_filter_ids = self.env['ks_dashboard_ninja.board_defined_filters'].search(
            [['id', 'in', self.ks_dashboard_defined_filters_ids.ids], '|', ['ks_is_active', '=', True],
             ['display_type', '=', 'line_section']], order='sequence')
        data = {}
        filter_model_ids = pre_defined_filter_ids.mapped('ks_model_id').ids
        for model_id in filter_model_ids:
            filter_ids = self.env['ks_dashboard_ninja.board_defined_filters'].search(
                [['id', 'in', pre_defined_filter_ids.ids], '|', ['ks_model_id', '=', model_id],
                 ['display_type', '=', 'line_section']],
                order='sequence')
            connect_symbol = '|'
            for rec in filter_ids:
                if rec.display_type == 'line_section':
                    connect_symbol = '&'

                if data.get(rec.ks_model_id.model) and rec.ks_domain:
                    data[rec.ks_model_id.model]['domain'] = data[rec.ks_model_id.model]['domain'] + safe_eval(
                        rec.ks_domain)
                    data[rec.ks_model_id.model]['domain'].insert(0, connect_symbol)
                elif rec.ks_model_id.model:
                    ks_domain = rec.ks_domain
                    if ks_domain and "%UID" in ks_domain:
                        ks_domain = ks_domain.replace('"%UID"', str(self.env.user.id))
                    if ks_domain and "%MYCOMPANY" in ks_domain:
                        ks_domain = ks_domain.replace('"%MYCOMPANY"', str(self.env.company.id))
                    data[rec.ks_model_id.model] = {
                        'domain': safe_eval(ks_domain) if ks_domain else [],
                        'ks_domain_index_data': [],
                        'model_name': rec.ks_model_id.name,
                        'item_ids': self.env['ks_dashboard_ninja.item'].search(
                            [['id', 'in', self.ks_dashboard_items_ids.ids], '|',
                             ['ks_model_id', '=', rec.ks_model_id.id], ['ks_model_id_2', '=', rec.ks_model_id.id]]).ids
                    }

        return data

    def ks_prepare_dashboard_pre_domain(self):
        data = {}
        pre_defined_filter_ids = self.env['ks_dashboard_ninja.board_defined_filters'].search(
            [['id', 'in', self.ks_dashboard_defined_filters_ids.ids]], order='sequence')
        categ_seq = 1
        for rec in pre_defined_filter_ids:
            if rec.display_type == 'line_section':
                categ_seq = categ_seq + 1
            ks_domain = rec.ks_domain
            if ks_domain and "%UID" in ks_domain:
                ks_domain = ks_domain.replace('"%UID"', str(self.env.user.id))
            if ks_domain and "%MYCOMPANY" in ks_domain:
                ks_domain = ks_domain.replace('"%MYCOMPANY"', str(self.env.company.id))

            data[rec['id']] = {
                'id': rec.id,
                'name': rec.name,
                'model': rec.ks_model_id.model,
                'model_name': rec.ks_model_id.name,
                'active': rec.ks_is_active,
                'categ': rec.ks_model_id.model + '_' + str(categ_seq) if rec.display_type != 'line_section' else 0,
                'type': 'filter' if rec.display_type != 'line_section' else 'separator',
                'domain': safe_eval(ks_domain) if ks_domain else [],
                'sequence': rec.sequence
            }
        return data

    def ks_prepare_dashboard_custom_domain(self):
        custom_filter_ids = self.env['ks_dashboard_ninja.board_custom_filters'].search(
            [['id', 'in', self.ks_dashboard_custom_filters_ids.ids]], order='name')
        data = {}
        for rec in custom_filter_ids:
            data[str(rec.id)] = {
                'id': rec.id,
                'name': rec.name,
                'model': rec.ks_model_id.model,
                'model_name': rec.ks_model_id.name,
                'field_name': rec.ks_domain_field_id.name,
                'field_type': rec.ks_domain_field_id.ttype,
                'special_data': {}
            }
            if rec.ks_domain_field_id.ttype == 'selection':
                data[str(rec.id)]['special_data'] = {
                    'select_options':
                        self.env[rec.ks_model_id.model].fields_get(allfields=[rec.ks_domain_field_id.name])[
                            rec.ks_domain_field_id.name]['selection']
                }
        return data
