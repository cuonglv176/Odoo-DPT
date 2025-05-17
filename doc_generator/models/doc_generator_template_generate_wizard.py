from odoo import models, fields, api, _


class DocGeneratorTemplateGenerateWizard(models.TransientModel):
    _name = 'doc.generator.template.generate.wizard'
    _description = 'Doc Generator Template Generate Wizard'

    template_id = fields.Many2one('doc.generator.template', string='Template')
    model_id = fields.Many2one('ir.model', string='Model', related='template_id.model_id')
    resource_ref = fields.Reference(selection='_selection_target_model', string='Record', copy=False)
    file_format = fields.Selection([('docx', 'DOCX'), ('pdf', 'PDF')], string='File Format', default='docx')

    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    def generate_document(self):
        return self.template_id.sudo().action_generate_document(resource_ref=self.resource_ref,
                                                                file_format=self.file_format)
