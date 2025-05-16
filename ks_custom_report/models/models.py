# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, sql_db
from odoo import tools
from odoo.exceptions import UserError, ValidationError
import json


class IrModel(models.Model):
    _inherit = 'ir.model'

    ks_is_custom_model = fields.Boolean(
        string="ReportMate Model", default=False,
        help="Whether this model supports custom report.",
    )

    @api.model
    def _instanciate(self, model_data):
        model_class = super(IrModel, self)._instanciate(model_data)
        if model_data.get('ks_is_custom_model', False):
            model_class._auto = False

        return model_class


class KsCustomReport(models.Model):
    _name = 'ks_custom_report.ks_report'
    _description = 'Report Model'

    name = fields.Char(string="Report Name", required=True)
    ks_model_id = fields.Many2one("ir.model", string="Model", ondelete='cascade',
                                  domain=[('access_ids', '!=', False), ('transient', '=', False),
                                          ('model', 'not ilike', 'base_import%'), ('model', 'not ilike', 'ir.%'),
                                          ('model', 'not ilike', 'web_editor.%'), ('model', 'not ilike', 'web_tour.%'),
                                          ('model', '!=', 'mail.thread'), ('model', 'not ilike', 'ks_%'),
                                          ('model', 'not ilike', 'ks_%')])

    ks_cr_model_id = fields.Many2one("ir.model", string="Report Model", ondelete='cascade', copy=False)

    # Views ---------------------------------
    ks_tree_view_id = fields.Many2one("ir.ui.view", string="Report Tree View", ondelete='set null', copy=False)
    ks_search_view_id = fields.Many2one("ir.ui.view", string="Report Search View", copy=False)
    ks_pivot_view_id = fields.Many2one("ir.ui.view", string="Report Pivot View", copy=False)

    ks_cr_column_ids = fields.One2many(comodel_name="ks_custom_report.ks_column", inverse_name="ks_cr_model_id",
                                       string="Report Fields")

    # Menu Fields ----------------
    ks_cr_menu_name = fields.Char(string="Menu Name", required=True)
    ks_cr_top_menu_id = fields.Many2one('ir.ui.menu', default=lambda self: self.env.ref('ks_custom_report.menu_root'),
                                        string="Show Under Menu", required=True)
    ks_cr_menu_priority = fields.Integer(string="Menu Priority", required=True, default=50)
    ks_cr_active = fields.Boolean(string="Active", default=True)
    ks_cr_group_access = fields.Many2many('res.groups', string="Group Access")

    ks_cr_menu_id = fields.Many2one('ir.ui.menu', string="cr Menu Id")
    ks_cr_action_id = fields.Many2one('ir.actions.act_window', string="Web Server Action Id")

    # Show Pivot and Graph View
    ks_show_pivot_view = fields.Boolean(string="Show Pivot View", default=True)
    ks_show_graph_view = fields.Boolean(string="Show Graph View", default=True)

    # selection  query field
    ks_cr_query_type = fields.Selection([('custom_query', 'Custom Query'), ('field_chain', 'Field Chain')],
                                        'Query Type', default='field_chain')
    ks_custom_query = fields.Text('Custom Query')
    ks_custom_query_report_column_ids = fields.One2many(comodel_name="ks.custom.query.report.column",
                                                        inverse_name="ks_cr_model_id",
                                                        string="Query Report Fields")
    ks_show_query_field_tree_view = fields.Boolean('Show Query Field Tree View', default=False, copy=False)
    ks_model_update = fields.Boolean('Field Chain Model Update', default=False, copy=False)

    def _check_ks_custom_query_type(self, query):
        if query:
            query = query.lower()
            if list(filter(lambda x: x in query, ['update', 'insert', 'delete',
                                                  'create', 'drop', 'alter',
                                                  'truncate', 'comment', 'rename', 'grant',
                                                  'revoke', 'commit', 'rollback', 'savepoint'])):
                raise UserError(
                    _("User are not allowed to modify the records through query. Please check your query again."))

    @api.onchange('ks_cr_query_type', 'ks_custom_query')
    def ks_onchange_on_ks_cr_query_type(self):
        if self.ks_cr_query_type == 'custom_query':
            ks_query = self.ks_custom_query
            if ks_query:
                field_list = self.ks_check_update_custom_query(ks_query)
                lines = [(5, 0, 0)]
                for rec in field_list[0]:
                    if not rec[0].startswith('x_') and not rec[0] == 'id':
                        raise ValidationError(_("Custom fields must have a name that starts with 'x_' !"))
                    vals = {'name': rec[0]}
                    lines.append((0, 0, vals))
                self.ks_custom_query_report_column_ids = lines
            else:
                self.ks_custom_query_report_column_ids = [(5, 0, 0)]
                self.ks_show_query_field_tree_view = False

            if self.ks_custom_query_report_column_ids:
                self.ks_show_query_field_tree_view = True

    @api.model
    def create(self, values):
        if values.get('ks_cr_query_type') == 'custom_query':
            self._check_ks_custom_query_type(values.get('ks_custom_query'))
        rec = super(KsCustomReport, self).create(values)
        self._ks_create_db_table(rec.sudo())
        self._ks_create_custom_report(rec.sudo())
        return rec

    def write(self, vals):
        if vals.get('ks_cr_query_type') == 'custom_query':
            vals['ks_model_id'] = False
            vals['ks_model_update'] = False

        if vals.get('ks_custom_query'):
            self._check_ks_custom_query_type(vals.get('ks_custom_query'))

        record = super(KsCustomReport, self).write(vals)
        for res in self:
            rec = res.sudo()
            if vals.get('ks_model_id') and rec.ks_model_update:
                raise UserError(_('Report Model cannot be changed after it is created !'))

            if any([vals.get('ks_cr_column_ids'), vals.get('ks_cr_query_type'), vals.get('ks_custom_query')]):
                self._ks_create_db_table(rec)

            if vals.get('name'):
                rec.ks_cr_action_id.name = vals.get('name')

            menu_update_vals = {}
            if 'ks_cr_menu_name' in vals:
                menu_update_vals['name'] = vals['ks_cr_menu_name']
            if 'ks_cr_group_access' in vals:
                menu_update_vals['groups_id'] = vals['ks_cr_group_access']
            if 'ks_cr_active' in vals and rec.ks_cr_menu_id:
                menu_update_vals['active'] = vals['ks_cr_active']
            if 'ks_cr_top_menu_id' in vals:
                menu_update_vals['parent_id'] = vals['ks_cr_top_menu_id']
            if 'ks_cr_menu_priority' in vals:
                menu_update_vals['sequence'] = vals['ks_cr_menu_priority']
            rec.ks_cr_menu_id.write(menu_update_vals)

            if rec.ks_cr_action_id:
                view_mode = rec.ks_cr_action_id.view_mode.split(",")
                if 'ks_show_pivot_view' in vals:
                    view_mode.append("pivot") if vals['ks_show_pivot_view'] else view_mode.remove("pivot")
                if 'ks_show_graph_view' in vals:
                    view_mode.append("graph") if vals['ks_show_graph_view'] else view_mode.remove("graph")
                rec.ks_cr_action_id.write({'view_mode': ",".join(view_mode)})
        return record

    def unlink(self):
        for res in self:
            rec = res.sudo()
            rec.ks_tree_view_id.unlink()
            rec.ks_search_view_id.unlink()
            rec.ks_pivot_view_id.unlink()

            rec.ks_cr_action_id.unlink()
            rec.ks_cr_menu_id.unlink()

            if rec.ks_cr_model_id:
                rec.ks_cr_model_id.unlink()

        return super(KsCustomReport, self).unlink()

    def _ks_create_custom_report(self, rec):
        # It Creates: Menu and Access Rights of the model
        self._ks_cr_menu_action(rec)
        self._ks_cr_access_rights(rec)

    def _ks_cr_model(self, rec, model_name):
        rec.ks_cr_model_id = self.env['ir.model'].sudo().create({
            'name': rec.name,
            'model': model_name,
            'state': 'manual',
            'ks_is_custom_model': True,
        })

    def _ks_cr_fields(self, rec, column_id, field_name, ir_field_id, display_name=False):
        ttype = 'float' if ir_field_id.ttype == 'monetary' else ir_field_id.ttype

        is_exist = self.env['ir.model.fields'].sudo().search(
            [('name', '=', field_name), ('model_id', '=', rec.ks_cr_model_id.id)])
        if is_exist:
            for fields_rec in is_exist:
                fields_rec.unlink()

        values = {
            'name': field_name,
            'ttype': ttype,
            'field_description': display_name if display_name else ir_field_id.field_description,
            'model_id': rec.ks_cr_model_id.id,
            'state': 'manual',
            'selection': ir_field_id.selection,
        }

        column_id.ks_cr_field_id = self.env['ir.model.fields'].sudo().create(values)

    def _ks_cr_menu_action(self, rec):
        cr_model = rec.ks_cr_model_id
        view_mode = ["tree", "form"]

        if rec.ks_show_pivot_view:
            view_mode.append("pivot")

        if rec.ks_show_graph_view:
            view_mode.append("graph")

        action_vals = {
            'name': rec.name,
            'res_model': cr_model.model,
            'view_mode': ",".join(view_mode),
            'views': [(False, 'tree'), (False, 'form')],
        }

        rec.ks_cr_action_id = self.env['ir.actions.act_window'].sudo().create(action_vals)

        rec.ks_cr_menu_id = self.env['ir.ui.menu'].sudo().create({
            'name': rec.ks_cr_menu_name,
            'parent_id': rec.ks_cr_top_menu_id.id,
            'action': 'ir.actions.act_window,%d' % (rec.ks_cr_action_id.id,),
            'groups_id': rec.ks_cr_group_access,
            'sequence': rec.ks_cr_menu_priority,
            'active': rec.ks_cr_active,
        })

    def _ks_cr_access_rights(self, rec):
        cr_model = rec.ks_cr_model_id
        self.env['ir.model.access'].sudo().create({
            'name': cr_model.name + ' all_user',
            'model_id': cr_model.id,
            'perm_read': True,
            'perm_write': False,
            'perm_create': False,
            'perm_unlink': False,
        })

    def _create_chain_query(self, rec):
        rec.ks_tree_view_id.unlink()
        rec.ks_search_view_id.unlink()
        rec.ks_pivot_view_id.unlink()

        field_list = []
        search_filter_field_list = ['id']
        group_filter_field_list = []
        default_group_filter_field_list = []

        select_clause_list = []
        from_clause_list = []
        custom_field_list = []
        sort_field_list = []
        display_field_list = []

        rec.ks_model_update = True
        ks_model = self.env['ir.model'].search([('model', '=', rec.ks_model_id.model)], limit=1)

        temp_model_name = ks_model.model

        query_data = {"".join([x[0] for x in temp_model_name.split(".")]): temp_model_name}

        from_clause_list.append(
            "_".join(temp_model_name.split(".")) + ' ' + "".join([x[0] for x in temp_model_name.split(".")]))

        current_abbr_chain = "".join([x[0] for x in temp_model_name.split(".")])
        select_clause_list.append(
            f'ROW_NUMBER () over(ORDER BY {current_abbr_chain}.id) as id')

        # x_name field default value set
        rec_name = 'id'
        select_clause_list.append("".join([x[0] for x in temp_model_name.split(".")]) + '.' +
                                  rec_name + '::varchar as x_name')

        for column_id in rec.ks_cr_column_ids:
            temp_model_name = ks_model.model

            ks_operator = column_id.ks_operator if column_id.ks_operator and column_id.ks_alter_values else ''
            ks_value = str(column_id.ks_value) if column_id.ks_value and column_id.ks_alter_values else ''

            ks_year = str(column_id.ks_year) + 'year' if column_id.ks_year and column_id.ks_alter_values else ''
            ks_month = str(column_id.ks_month) + 'month' if column_id.ks_month and column_id.ks_alter_values else ''
            ks_week = str(column_id.ks_week) + 'week' if column_id.ks_week and column_id.ks_alter_values else ''
            ks_day = str(column_id.ks_day) + 'day' if column_id.ks_day and column_id.ks_alter_values else ''
            ks_hour = str(column_id.ks_hour) + 'hour' if column_id.ks_hour and column_id.ks_alter_values else ''

            current_abbr_chain = "".join([x[0] for x in temp_model_name.split(".")])
            field_chain = column_id.ks_model_field_chan.split(".")

            for field in field_chain:
                field_id = self.env['ir.model.fields'].search(
                    [('model', '=', temp_model_name), ('name', '=', field)])
                if field_id.relation:
                    prev_abbr = current_abbr_chain
                    current_abbr_chain = current_abbr_chain + '_' + "".join(
                        [x[0] for x in field_id.relation.split(".")])
                    temp_model_name = field_id.relation

                    if query_data.get(current_abbr_chain) != field_id.relation:
                        i = 1
                        while query_data.get(current_abbr_chain) and query_data.get(
                                current_abbr_chain) != field_id.relation:
                            current_abbr_chain += str(i)
                            i += 1
                            while query_data.get(current_abbr_chain):
                                current_abbr_chain += str(i)

                        query_data[current_abbr_chain] = field_id.relation

                        if field_id.ttype == 'one2many':
                            join_type = 'left join '
                            join_condition = ' on %s = %s' % (
                                current_abbr_chain + '.' + field_id.relation_field, prev_abbr + '.id')

                            from_clause_list.append(join_type + "_".join(
                                temp_model_name.split(".")) + ' ' + current_abbr_chain + ' ' + join_condition)
                        elif field_id.ttype == 'many2many':
                            attrs = {}
                            rel, col1, col2 = self.ks_many2many_names(field_id['model'], field_id['relation'])
                            attrs['relation'] = field_id['relation_table'] or rel
                            attrs['column1'] = field_id['column1'] or col1
                            attrs['column2'] = field_id['column2'] or col2
                            rel_chain = current_abbr_chain + "_rel"

                            from_clause_list.append(
                                'left join ' + attrs['relation'] + ' ' + rel_chain + ' on ' + rel_chain + '.' +
                                attrs[
                                    'column1'] + '=' + prev_abbr + '.id')

                            from_clause_list.append('left join ' + "_".join(
                                temp_model_name.split(".")) + ' ' + current_abbr_chain + ' on ' + rel_chain + '.' +
                                                    attrs['column2'] + '=' + current_abbr_chain + '.id')
                        else:
                            join_type = 'left join '
                            join_condition = ' on %s = %s' % (
                                prev_abbr + '.' + field_id.name, current_abbr_chain + '.id')

                            from_clause_list.append(join_type + "_".join(
                                temp_model_name.split(".")) + ' ' + current_abbr_chain + ' ' + join_condition)

            if query_data.get(current_abbr_chain):
                field = field_chain[-1]
                field_id = self.env['ir.model.fields'].search(
                    [('model', '=', temp_model_name), ('name', '=', field)])
                ks_field_name = 'x_ks_' + field
                i = 1

                while ks_field_name in field_list:
                    ks_field_name = 'x_ks_' + str(i) + '_' + field
                    i += 1

                field_list.append(ks_field_name)

                if column_id.ks_incl_display:
                    display_field_list.append(ks_field_name)
                    if column_id.ks_incl_sort:
                        sort_field_list.append(ks_field_name + ' ' + column_id.sortable_type)
                if column_id.ks_incl_search_filter:
                    search_filter_field_list.append(ks_field_name)
                if column_id.ks_incl_group_filter:
                    group_filter_field_list.append(ks_field_name)
                    if column_id.ks_incl_default_group_filter:
                        default_group_filter_field_list.append(ks_field_name)

                if (field_id.ttype == 'datetime' or field_id.ttype == 'date') and any(
                        [ks_year, ks_month, ks_week, ks_day, ks_hour]):
                    field = "coalesce(%s, (now() at time zone 'UTC'))" % (current_abbr_chain + '.' + json.dumps(
                        field)) + ' + interval ' + "'" + ' ' + ks_year + ' ' + ks_month + ' ' + ks_week + ' ' + ks_day + ' ' + ks_hour + "'"
                    if field_id.ttype == 'date':
                        field = "Date(" + field + ")"
                    select_clause_list.append(field + ' as ' + json.dumps(ks_field_name))
                elif field_id.ttype in ['integer', 'float', 'monetary'] and any([ks_operator, ks_value]):
                    field = 'coalesce(%s, 0)' % (current_abbr_chain + '.' + json.dumps(field)) + ks_operator + ks_value
                    select_clause_list.append(field + ' as ' + json.dumps(ks_field_name))
                else:
                    if field_id.translate:
                        lang = self.env.user.lang
                        select_clause_list.append(
                            current_abbr_chain + '.' + json.dumps(
                                field) + '->>' + "'" + lang + "'" + ' ::varchar' + ' as ' + json.dumps(
                                ks_field_name))
                    else:
                        select_clause_list.append(
                            current_abbr_chain + '.' + json.dumps(field) + ' as ' + json.dumps(ks_field_name))

                custom_field_list.append((rec, column_id, ks_field_name, field_id, column_id.name))
        sort_by_string = ''
        if sort_field_list:
            sort_by_string = 'order by ' + ','.join(sort_field_list)
        ks_query = 'SELECT %s FROM %s %s' % (",".join(select_clause_list), " ".join(from_clause_list), sort_by_string)
        self.ks_query_validate(ks_query)
        return [ks_query, custom_field_list, field_list, search_filter_field_list, group_filter_field_list,
                sort_field_list, display_field_list, default_group_filter_field_list]

    def ks_unlink_fields(self, rec):
        search_id = self.env['ir.ui.view'].search([('model', '=', rec.ks_cr_model_id.model), ('type', '=', 'search')])
        search_id.unlink()
        if rec.ks_cr_query_type == 'field_chain':
            for record in rec.ks_custom_query_report_column_ids:
                record.unlink()
        if rec.ks_cr_query_type == 'custom_query':
            for record in rec.ks_cr_column_ids:
                record.unlink()

        field_rec = [i for i in self.env['ir.model.fields'].sudo().search([('model_id', '=', rec.ks_cr_model_id.id)]) if
                     i.name.startswith('x_')]
        for field in field_rec:
            if field.name != 'x_name' and field.name != 'id':
                field.unlink()

    def ks_create_custom_fields(self, rec, header_rec):
        self.ks_unlink_fields(rec)
        for field in header_rec:
            ks_field_type = self.ks_get_type_of_field(field)
            ks_translate = False
            if ks_field_type == 'json':
                ks_field_type = 'char'
                ks_translate = True
            if field[0] != 'x_name' and rec.ks_cr_model_id and field[0] != 'id':
                field_id = self.env['ir.model.fields'].create({
                    'name': field[0],
                    'model_id': rec.ks_cr_model_id.id,
                    'state': 'manual',
                    'ttype': ks_field_type,
                    'translate': ks_translate
                })

        for field, col in zip(header_rec, rec.ks_custom_query_report_column_ids):
            col.write({'name': field[0], 'ks_cr_model_id': rec.id})
        for field in header_rec:
            if field[0] not in rec.ks_custom_query_report_column_ids.mapped('name'):
                self.env['ks.custom.query.report.column'].create({'name': field[0], 'ks_cr_model_id': rec.id})
        if rec.ks_custom_query_report_column_ids:
            rec.ks_show_query_field_tree_view = True

    def ks_get_type_of_field(self, field):
        if field[1] == 1043:
            return 'char'
        elif field[1] == 16:
            return 'boolean'
        elif field[1] == 1082:
            return 'date'
        elif field[1] == 1114:
            return 'datetime'
        elif field[1] == 23:
            return 'integer'
        elif field[1] == 3802:
            return 'json'
        elif field[1] == 25:
            return 'text'
        else:
            return 'float'

    def _ks_create_db_table(self, rec):
        # Drop table if exist. Create/Fetch query. Then create table after the query is ready.,

        cr_model_name = rec.ks_cr_model_id.model
        table = self.env[cr_model_name]._table if cr_model_name else False
        if not table:
            if rec.ks_cr_query_type == 'custom_query':
                table = self.env['ir.sequence'].next_by_code('custom.query.report')
            else:
                table = "x_ks_cr_ks_" + "".join([x[0] for x in rec.ks_model_id.model.split(".")]) + str(rec.id)

        tools.drop_view_if_exists(self.env.cr, table)

        if rec.ks_cr_query_type == 'field_chain':
            table_query = self._create_chain_query(rec)
        else:
            table_query = self._create_custom_query(rec)

        self._cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (table, table_query[0]))

        if not cr_model_name:
            self._ks_cr_model(rec, table)

        if rec.ks_cr_query_type == 'field_chain':
            self.ks_unlink_fields(rec)
            for column_id in rec.ks_cr_column_ids:
                column_id.ks_cr_field_id.unlink()
            for field in table_query[1]:
                self._ks_cr_fields(field[0], field[1], field[2], field[3], field[4])
            self.ks_create_tree_view(rec, table_query[6], table_query[5])
            self.ks_create_search_filter_view(rec, table_query[3], table_query[4], table_query[7])
        else:
            self.ks_create_custom_fields(rec, table_query[1])
            self.ks_create_tree_view(rec, table_query[6], table_query[5])

    def ks_check_update_custom_query(self, ks_query):
        field_name_with_type_code = []
        field_list = []
        if ks_query:
            ks_query = ks_query.lower()
            ks_name_flag = False
            ks_id_flag = False
            if 'union all' in ks_query or 'union' in ks_query:
                if 'union all' in ks_query:
                    query_parts = ks_query.split("union all")
                    joins = " UNION ALL "
                else:
                    query_parts = ks_query.split("union")
                    joins = " UNION "

                queries = []
                for query in query_parts:
                    if 'select' in query:
                        index_value = query.index('select') + 7
                        if 'row_number' not in query and 'as id' not in query:
                            if 'x_name' not in query:
                                query = query[:index_value] + "row_number() over() as id, '' as x_name," + query[
                                                                                                           index_value:]
                                ks_name_flag = True
                                ks_id_flag = True
                            else:
                                query = query[:index_value] + 'row_number() over() as id,' + query[index_value:]
                                ks_id_flag = True
                            queries.append(query)

                        else:
                            if 'x_name' not in query:
                                query = query[:index_value] + " '' as x_name," + query[index_value:]
                                ks_name_flag = True
                            queries.append(query)
                ks_query = joins.join(queries)
            elif 'select' in ks_query:
                index_value = ks_query.index('select') + 7
                if 'row_number' not in ks_query and 'as id' not in ks_query:
                    if 'x_name' not in ks_query:
                        ks_query = ks_query[:index_value] + "row_number() over() as id, '' as x_name," + ks_query[
                                                                                                         index_value:]
                        ks_name_flag = True
                        ks_id_flag = True
                    else:
                        ks_query = ks_query[:index_value] + 'row_number() over() as id,' + ks_query[index_value:]
                        ks_id_flag = True
                else:
                    if 'x_name' not in ks_query:
                        ks_query = ks_query[:index_value] + " '' as x_name," + ks_query[index_value:]
                        ks_name_flag = True
            field_name_with_type_code = self.ks_query_validate(ks_query)
            field_list = [i[0] for i in field_name_with_type_code]
            field_list = field_list[2:] if ks_name_flag and ks_id_flag else field_list[1:] if ks_name_flag \
                else field_list[1:] if ks_id_flag else field_list
            field_name_with_type_code = field_name_with_type_code[
                                        2:] if ks_name_flag and ks_id_flag else field_name_with_type_code[
                                                                                1:] if ks_name_flag \
                else field_name_with_type_code[1:] if ks_id_flag else field_name_with_type_code

        return [field_name_with_type_code, field_list, ks_query]

    def _create_custom_query(self, rec):
        rec.ks_tree_view_id.unlink()
        rec.ks_search_view_id.unlink()
        rec.ks_pivot_view_id.unlink()
        field_list = self.ks_check_update_custom_query(rec.ks_custom_query)
        ks_query = field_list[2]
        return [ks_query, field_list[0], field_list[1]]

    # Tree View override to show all fields in list view
    def ks_create_tree_view(self, rec, field_list, sort_field_list):
        cr_model = rec.ks_cr_model_id
        rec.ks_tree_view_id = self.env['ir.ui.view'].sudo().create({
            'name': rec.name + ' List View',
            'model': cr_model.model,
            'arch': '<tree string="%s" default_order="%s" >' % (
                rec.name + ' List View', ",".join(sort_field_list)) + "\n".join(
                ['<field name="%s"/>' % x for x in field_list]) + '</tree>',
        })

    def ks_group_filter_arch(self, fields_desc, search_filter_field_list, group_filter_field_list, name, model):
        """
            Creates arch for search view and group filter.
        """

        group_arch = '<group expand="0" string="Group By">' + \
                     "\n".join(['<filter name="group_%s" string="%s" context="%s"/>' % (
                         x, fields_desc.get(x).string, "{'group_by': '%s'}" % x) for x in group_filter_field_list]) + \
                     '</group>'

        search_filter_arch = "\n".join(['<field name="%s"/>' % x for x in search_filter_field_list])

        values = {
            'name': name + ' Search View',
            'model': model,
            'arch': '<search string="%s">' % (
                    'Search ' + name) + search_filter_arch + group_arch + '</search>',
        }
        return values

    def ks_create_search_filter_view(self, rec, search_filter_field_list, group_filter_field_list,
                                     default_group_filter_field_list):
        cr_model = rec.ks_cr_model_id
        fields_desc = self.env[cr_model.model]._fields
        rec.ks_search_view_id = self.env['ir.ui.view'].search([('model', '=', cr_model.model), ('type', '=', 'search')])
        values = self.ks_group_filter_arch(fields_desc, search_filter_field_list, group_filter_field_list, rec.name,
                                           cr_model.model)

        if rec.ks_search_view_id:
            rec.ks_search_view_id.write(values)
        else:
            rec.ks_search_view_id = self.env['ir.ui.view'].sudo().create(values)
        context = {}
        for default_group_filter_field in default_group_filter_field_list:
            context.update({
                f'search_default_group_{default_group_filter_field}': True,
            })
        rec.ks_cr_action_id.write({
            'context': context
        })

    def ks_many2many_names(self, model_name, relation):
        """ Return default names for the table and columns of a custom many2many field. """
        rel1 = self.env[model_name]._table
        rel2 = self.env[relation]._table
        table = '%s_%s_rel' % tuple(sorted([rel1, rel2]))
        if rel1 == rel2:
            return (table, 'id1', 'id2')
        else:
            return (table, '%s_id' % rel1, '%s_id' % rel2)

    # To remove columns if model is changed
    @api.onchange('ks_model_id')
    def _onchange_ks_model(self):
        for rec in self:
            rec.ks_cr_column_ids = False

    def ks_query_validate(self, ks_query):
        with api.Environment.manage():
            try:
                new_cr = self.pool.cursor()
                new_cr.execute(ks_query)
                header_rec = [(col.name, col.type_code) for col in new_cr.description]
            except Exception as e:
                raise UserError(_(e))
            finally:
                new_cr.close()

        if header_rec:
            return header_rec

    @api.constrains('ks_cr_column_ids')
    def _ks_check_field_chain(self):
        for rec in self:
            if rec.ks_cr_query_type == 'field_chain' and len(rec.ks_cr_column_ids.ids) == 0:
                raise ValidationError(_("Report can not be blank, please select at least one column in the report"))
