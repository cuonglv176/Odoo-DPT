from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DocGeneratorTemplate(models.Model):
    _name = 'doc.generator.template'
    _inherit = 'mail.thread'
    _description = 'Doc Generator Template'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    template_docx = fields.Binary(string='Template Docx', attachment=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    res_model = fields.Char(string='Model Name', compute='_compute_res_model', store=True, readonly=False)
    resource_ref = fields.Reference(selection='_selection_target_model', string='Record', copy=False)
    res_id = fields.Integer(string='Record ID', compute='_compute_res_id', store=True)
    line_ids = fields.One2many('doc.generator.template.line', 'template_id', string='Lines', copy=True)
    readonly_line_ids = fields.One2many('doc.generator.template.line', 'template_id', string='Lines')
    has_write_access = fields.Boolean(compute='_compute_has_write_access', string='Has Write Access', compute_sudo=True)
    template_docx_name = fields.Char(string='Template Docx Name')
    user_id = fields.Many2one('res.users', string='User')
    markup_ids = fields.Many2many('doc.generator.markup', string='Markups', compute='_compute_markup_ids')
    # Versioning
    version_number = fields.Char('Version No.', compute='_compute_version_number', store=True)
    last_version_id = fields.Many2one('doc.generator.template.version', string='Last Version',
                                      compute='_compute_last_version_id', store=True)
    version_ids = fields.One2many('doc.generator.template.version', 'template_id', string='Versions')
    major_version_number = fields.Integer('Major Version Number')
    minor_version_number = fields.Integer('Minor Version Number')
    submit_number = fields.Integer('Revision Number')
    document_ids_count = fields.Integer(compute='_compute_document_ids_count', string='Documents Count',
                                        compute_sudo=True)

    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    def button_submit(self):
        if not self.template_docx:
            raise UserError(_('Please upload a template file.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'doc.generator.template.submit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_major_version_number': self.major_version_number or 0,
                'default_minor_version_number': self.minor_version_number + 1,
                'default_submit_number': self.submit_number + 1,
            },
        }

    def button_generate_document(self):
        if not self.template_docx:
            raise UserError(_('Please upload a template file.'))
        return {
            'name': 'Generate Document',
            'type': 'ir.actions.act_window',
            'res_model': 'doc.generator.template.generate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_model_id': self.model_id.id,
            },
        }

    def action_submit(self, **kwargs):
        self.write({
            'major_version_number': kwargs.get('major_version_number'),
            'minor_version_number': kwargs.get('minor_version_number'),
            'submit_number': kwargs.get('submit_number'),
        })
        self._create_version(**kwargs)

    def _create_version(self, **kwargs):
        version = self.env['doc.generator.template.version'].create({
            'template_id': self.id,
            'major_version_number': self.major_version_number,
            'minor_version_number': self.minor_version_number,
            'submit_number': self.submit_number,
            'submit_date': fields.Datetime.now(),
            'description': kwargs.get('description', ''),
        })
        if self.template_docx:
            version.attachment_ids = self._get_version_attachment_data()

    def _get_version_attachment_data(self):
        return [(0, 0, {
            'name': self.template_docx_name,
            'datas': self.template_docx,
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
        })]

    # def action_duplicate_template(self):
    #     new_template = self.sudo().copy({'name': '%s (New)' % self.name, 'user_id': self.env.user.id})
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': self._name,
    #         'res_id': new_template.id,
    #         'view_mode': 'form',
    #         'target': 'current',
    #     }

    def action_check_value(self):
        self = self.sudo().with_context(read_text_only=True)
        if not self.resource_ref:
            raise UserError(_('Record is missing!'))
        context = self.resource_ref.read()[0]
        for line in self.line_ids:
            if line.field_id:
                field = line.field_id
                if field.ttype == 'one2many':
                    value = _('Table View')
                else:
                    value = context[field.name]
                line.value = str(value)

    def action_generate_document(self, resource_ref=None, extra_data=None, file_format='docx'):
        if extra_data is None:
            extra_data = {}
        self = self.sudo()
        template_docx_attachment = self.env['ir.attachment'].search(
            [('res_model', '=', self._name), ('res_id', '=', self.id), ('res_field', '=', 'template_docx')], limit=1)
        if not template_docx_attachment:
            raise UserError(_('Template is missing!'))
        report_name = 'doc_generator.doc_generator_template' if file_format == 'docx' else 'doc_generator.doc_generator_template_pdf'
        template_docx_path = template_docx_attachment._full_path(template_docx_attachment.store_fname)
        report_action = self.env['ir.actions.report']._get_report_from_name(report_name).report_action([], data={
            'template_docx_path': template_docx_path})
        resource_ref = resource_ref or self.resource_ref
        if not resource_ref:
            default_data = self._get_default_data()
            report_action['data']['default_data'] = default_data
        else:
            report_action['report_name'] += '/%s/%s' % (self.res_model, resource_ref.id)
        report_action['data']['markup_data'] = self.env['doc.generator.markup']._get_markup_data()
        report_action['data']['markup_data'].update(extra_data)
        return report_action

    def _get_default_data(self):
        default_data = {}
        for line in self.line_ids:
            if line.field_id:
                field = line.field_id
                if field.ttype == 'one2many':
                    value = [{child.field_id.name: child.default_value for child in line.child_ids}]
                else:
                    value = line.default_value
                default_data[field.name] = value
        return default_data

    def _compute_has_write_access(self):
        for record in self:
            record.has_write_access = self.user_has_groups(
                'doc_generator.group_doc_generator_manager,base.group_system')

    @api.onchange('res_model')
    def _onchange_res_model(self):
        self.model_id = self.env['ir.model'].sudo().search([('model', '=', self.res_model)], limit=1).id

    @api.depends('model_id')
    def _compute_res_model(self):
        for record in self:
            record.res_model = record.model_id.model

    @api.depends('resource_ref')
    def _compute_res_id(self):
        for record in self:
            record.res_id = record.resource_ref.id if record.resource_ref else False

    def _compute_document_ids_count(self):
        for record in self:
            record.document_ids_count = self.env['documents.document'].search_count(
                [('res_model', '=', self._name), ('res_id', '=', record.id)])

    @api.depends('major_version_number', 'minor_version_number')
    def _compute_version_number(self):
        for record in self:
            record.version_number = '%s.%s' % (record.major_version_number, record.minor_version_number)

    @api.depends('version_ids')
    def _compute_last_version_id(self):
        for record in self:
            record.last_version_id = record.version_ids[:1]

    def _compute_markup_ids(self):
        for record in self:
            record.markup_ids = self.env['doc.generator.markup'].search([])

    def action_view_document(self):
        kanban_view = self.env.ref('documents.document_view_kanban', False)
        search_view = self.env.ref('documents.document_view_search', False)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'documents.document',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'view_mode': 'kanban',
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
            'view_id': kanban_view and kanban_view.id,
            'search_view_id': search_view and [search_view.id],
        }


class DocGeneratorTemplateLine(models.Model):
    _name = 'doc.generator.template.line'
    _description = 'Doc Generator Template Line'
    _rec_name = 'key'
    _order = 'sequence'

    state = fields.Selection([('normal', 'Normal'), ('table', 'Table')], string='State', compute='_compute_state',
                             store=True)
    key = fields.Char('Dynamic Content')
    description = fields.Text('Description')
    value = fields.Text('Dynamic Value', copy=False)
    template_id = fields.Many2one('doc.generator.template', string='Template')
    field_id = fields.Many2one('ir.model.fields', string='Field', required=True, ondelete='cascade')
    name = fields.Char('Name')
    scope = fields.Char('Scope')
    default_value = fields.Text('Default Value')
    sequence = fields.Integer('Sequence')
    parent_id = fields.Many2one('doc.generator.template.line', string='Parent')
    child_ids = fields.One2many('doc.generator.template.line', 'parent_id', string='Children', copy=True)
    readonly_child_ids = fields.One2many('doc.generator.template.line', 'parent_id', string='Children')
    resource_ref = fields.Reference(string='Record', related='template_id.resource_ref', copy=False)
    model_id = fields.Many2one('ir.model', string='Model', related='template_id.model_id')
    res_model = fields.Char('Model')
    relation_model = fields.Char('Relation Model', related='field_id.relation', store=True)
    relation_ref = fields.Reference(string='Relation Reference', selection='_selection_target_model',
                                    compute='_compute_relation_ref', compute_sudo=True)
    has_write_access = fields.Boolean(related='template_id.has_write_access', string='Has Write Access')

    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    @api.onchange('field_id', 'resource_ref')
    def onchange_field_id(self):
        if self.field_id.ttype == 'one2many' and not self.parent_id:
            key = '{%%tr for line in %s%%} Table Dynamic Contents {%%tr endfor %%}' % self.field_id.name
        else:
            key = '{{%s%s}}' % ('line.' if self.parent_id else '', self.field_id.name) if self.field_id else ''
        update_values = {
            'key': key,
            'description': self.field_id.help,
            'name': self.field_id.field_description,
            'default_value': 'Default %s' % self.field_id.field_description if self.field_id else '',
        }
        self.write(update_values)

    def action_open_form_view(self):
        return {
            'name': _('Table View Config'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('doc_generator.doc_generator_template_line_view_form').id,
            'target': 'new',
        }

    def action_open_readonly_form_view(self):
        return {
            'name': _('Table View Config'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('doc_generator.doc_generator_template_line_readonly_view_form').id,
            'target': 'new',
        }

    def action_check_value(self):
        self = self.sudo().with_context(read_text_only=True)
        if self.relation_ref:
            context = self.relation_ref.read()[0]
            for line in self.child_ids:
                if line.field_id:
                    field = line.field_id
                    if field.ttype == 'one2many':
                        value = _('Table View')
                    else:
                        value = context[field.name]
                    line.value = str(value)
        return self.action_open_form_view()

    @api.depends('field_id.ttype')
    def _compute_state(self):
        for record in self:
            record.state = 'table' if record.field_id.ttype == 'one2many' else 'normal'

    @api.depends('resource_ref', 'field_id')
    def _compute_relation_ref(self):
        for record in self:
            if record.resource_ref and record.field_id.ttype == 'one2many':
                one2many_record = record.resource_ref[record.field_id.name][:1]
                record.relation_ref = '%s,%s' % (
                    record.field_id.relation, one2many_record.id) if one2many_record else False
            else:
                record.relation_ref = False
