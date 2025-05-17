from odoo import models, fields, api, _


class DocGeneratorTemplateSubmitWizard(models.TransientModel):
    _name = 'doc.generator.template.submit.wizard'
    _description = 'Doc Generator Template Submit Wizard'

    template_id = fields.Many2one('doc.generator.template', string='Template')
    major_version_number = fields.Integer('Major Version Number')
    minor_version_number = fields.Integer('Minor Version Number')
    submit_number = fields.Integer('Revision Number')
    description = fields.Html('Description')

    def submit_template(self):
        data = {
            'major_version_number': self.major_version_number,
            'minor_version_number': self.minor_version_number,
            'description': self.description,
            'submit_number': self.submit_number,
        }
        self.template_id.sudo().action_submit(**data)