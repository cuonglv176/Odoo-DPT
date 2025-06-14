from odoo import fields, models, api, _
from odoo.exceptions import UserError


class KsCrColumn(models.Model):
    _name = 'ks_custom_report.ks_column'
    _description = 'Report Field'
    _order = 'sequence'

    name = fields.Char(string="Field Name", required=True)
    ks_cr_model_id = fields.Many2one(comodel_name="ks_custom_report.ks_report", string="Report Model", ondelete='cascade')
    ks_model_field_chan = fields.Char(string="Field Chain", required=True, default="id")
    ks_model_name = fields.Char(compute='_onchange_ks_cr_model_id', string="Model Name")
    ks_cr_field_id = fields.Many2one("ir.model.fields", string="Report Field")

    # Search Group Filter field
    ks_incl_search_filter = fields.Boolean(string="Search Filter", default=True)
    ks_incl_group_filter = fields.Boolean(string="Group Filter", default=True)
    ks_incl_sort = fields.Boolean(string="Sortable", default=False)
    ks_incl_display = fields.Boolean(string=_("Display on View"), default=True)
    sortable_type = fields.Selection([('asc', _('Ascending')), ('desc', _('Descending'))], string=_("Sort Type"), default='asc')
    sequence = fields.Integer("Sequence",
                              default=lambda self: self.env['ir.sequence'].next_by_code('ks_custom_report.ks_column'))

    ks_operator = fields.Selection([('+', '+'), ('-', '-'), ('*', '*'), ('/', '/')], 'Operator', default='+')
    ks_value = fields.Float(string='Value', copy=False)
    ks_visible_operator_fields = fields.Boolean('Make visible Operator Fields', default=False)
    ks_visible_date_fields = fields.Boolean('Make visible Date Fields', default=False)
    ks_alter_values = fields.Boolean('Alter Values', default=False)
    ks_year = fields.Integer('Year')
    ks_month = fields.Integer('Month')
    ks_week = fields.Integer('Week')
    ks_day = fields.Integer('Day')
    ks_hour = fields.Integer('Hour')

    ks_incl_default_group_filter = fields.Boolean(string="Default Group", default=False)

    @api.onchange('ks_alter_values')
    def _onchange_ks_alter_values(self):
        if not self.ks_alter_values:
            self.ks_operator = self.ks_value = self.ks_year = self.ks_month = self.ks_week = self.ks_day = \
                self.ks_hour = False

    @api.onchange('ks_model_field_chan')
    def _onchange_ks_model_field_chan(self):
        model_name = self.ks_model_name
        count = 0
        ttype = False
        self.ks_visible_date_fields = False
        self.ks_visible_operator_fields = False
        field_chain = self.ks_model_field_chan.split(".")
        if not (len(field_chain) == 1 and field_chain[0] == 'id'):
            for field in field_chain:
                count += 1
                field_id = self.env['ir.model.fields'].search([('model', '=', model_name), ('name', '=', field)])
                model_name = field_id.relation
                if len(field_chain) == count:
                    ttype = field_id.ttype
        if ttype in ['integer', 'float', 'monetary']:
            self.ks_visible_operator_fields = True
        if ttype in ['datetime', 'date']:
            self.ks_visible_date_fields = True

    @api.onchange('ks_cr_model_id')
    def _onchange_ks_cr_model_id(self):
        if self.ks_cr_model_id.ks_model_id.id:
            self.ks_model_name = self.ks_cr_model_id.ks_model_id.model

    def unlink(self):
        for rec in self:
            rec.ks_cr_model_id.ks_tree_view_id.sudo().unlink()
            rec.ks_cr_model_id.ks_search_view_id.sudo().unlink()
            rec.ks_cr_model_id.ks_pivot_view_id.sudo().unlink()

            rec.ks_cr_field_id.sudo().unlink()
            return super(KsCrColumn, self).unlink()

    # Handling (checking) Invalid Field chan
    def write(self, values):
        for rec in self:
            if rec.ks_cr_model_id and values.get('ks_model_field_chan'):
                model = self.env[rec.ks_cr_model_id.ks_model_id.model]
                field_chain = values['ks_model_field_chan'].split(".")
                values['ks_model_field_chan'] = ".".join(self.ks_fallback_field(model, field_chain))
        return super(KsCrColumn, self).write(values)

    @api.model
    def create(self, values):
        if values.get('ks_cr_model_id') and values.get('ks_model_field_chan'):
            model = self.env[self.ks_cr_model_id.browse(values.get('ks_cr_model_id')).ks_model_id.model]
            field_chain = values['ks_model_field_chan'].split(".")
            values['ks_model_field_chan'] = ".".join(self.ks_fallback_field(model, field_chain))
        return super(KsCrColumn, self).create(values)

    def ks_fallback_field(self, model, field_chain):
        """
        Recursive Function for relation field to find fallback name field
        :param model: odoo_model class object
        :param field_chain: list
        :return: list
        """

        tmp_model_name = False
        for field in field_chain:
            tmp_model_name = model._fields.get(field).comodel_name
            model = self.env[tmp_model_name] if tmp_model_name else model

        if tmp_model_name:
            rec_name = model._rec_name_fallback()
        else:
            rec_name = field_chain[-1]

        if model._fields.get(rec_name).store:
            field_chain.append(rec_name) if rec_name not in field_chain else field_chain

        elif model._fields.get(rec_name).related:
            field_chain.extend(self.ks_fallback_field(model, model._fields.get(rec_name).related.split('.')))
        else:
            field_chain.append('id')

        return field_chain


class KsCrColumnReport(models.Model):
    _name = 'ks.custom.query.report.column'
    _description = 'Report Field'

    name = fields.Char(string="Field Name", copy=False)
    ks_display_name = fields.Char(string="Field Display Name", copy=False)
    search_by = fields.Boolean(string="Search Filter", copy=False)
    group_by = fields.Boolean(string="Group Filter", copy=False)
    ks_cr_model_id = fields.Many2one(comodel_name="ks_custom_report.ks_report", string="Query Report Model", copy=False, ondelete='cascade')

    def name_get(self):
        result = []
        for rec in self:
            name = '%s' % (rec.name if not rec.ks_display_name else rec.ks_display_name)
            result.append((rec.id, name))
        return result

    def write(self, vals):
        res = super(KsCrColumnReport, self).write(vals)
        field = self.env['ir.model.fields'].search(
            [('name', '=', self.name), ('model_id', '=', self.ks_cr_model_id.ks_cr_model_id.id)])
        if vals.get('ks_display_name') == False:
            ks_display_name = self.ks_get_field_display_name()
            field.field_description = ks_display_name
        elif self.ks_display_name:
            field.field_description = self.ks_display_name
        self.ks_create_update_search_filter_view()
        return res

    def ks_get_field_display_name(self):
        field_desc = ''
        field_name = [i.capitalize() for i in self.name.split('_')]
        for name in field_name:
            if self.name == 'x_name' and name == 'X':
                continue
            field_desc += name + ' '
        return field_desc

    def ks_create_update_search_filter_view(self):

        """ This function used to create and update search filter and group by filter """

        search_view_id = self.env['ir.ui.view'].search(
            [('model', '=', self.ks_cr_model_id.ks_cr_model_id.model), ('type', '=', 'search')])
        fields_desc = self.env[self.ks_cr_model_id.ks_cr_model_id.model]._fields
        ks_custom_fields = self.env['ks.custom.query.report.column'].search(
            [('ks_cr_model_id', '=', self.ks_cr_model_id.id)])

        search_filter_field_list = [i.name for i in ks_custom_fields if i.search_by and i.name] + ['id']
        group_by_field_list = [i.name for i in ks_custom_fields if i.group_by and i.name]

        if search_filter_field_list or group_by_field_list:
            values = self.ks_cr_model_id.ks_group_filter_arch(fields_desc, search_filter_field_list,
                                                              group_by_field_list, self.ks_cr_model_id.name, self.ks_cr_model_id.ks_cr_model_id.model)
            if search_view_id:
                search_view_id.write(values)
            else:
                self.ks_cr_model_id.ks_search_view_id = self.env['ir.ui.view'].sudo().create(values)