from odoo import models, fields, api, _


class DocGeneratorTemplateVersion(models.Model):
    _name = 'doc.generator.template.version'
    _rec_name = 'version_number'
    _order = 'template_id, submit_number desc'

    template_id = fields.Many2one('doc.generator.template', string='Template')
    name = fields.Char('Name', compute='_compute_name', store=True)
    version_number = fields.Char('Version No.', compute='_compute_version_number', store=True)
    major_version_number = fields.Integer('Major Version Number')
    minor_version_number = fields.Integer('Minor Version Number')
    submit_number = fields.Integer('Revision Number')
    submit_date = fields.Datetime('Submit Date')
    description = fields.Html('Description')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.depends('major_version_number', 'minor_version_number')
    def _compute_version_number(self):
        for record in self:
            record.version_number = '%s.%s' % (record.major_version_number, record.minor_version_number)

    @api.depends('template_id', 'version_number')
    def _compute_name(self):
        for record in self:
            record.name = '%s_v%s#%s_%s' % (record.template_id.name, record.version_number, record.submit_number,
                                            record.submit_date.strftime('%Y%m%d%H%M%S'))
