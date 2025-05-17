import json

from docxtpl import RichText

from odoo import models, fields, api, _


class DocGeneratorMarkup(models.Model):
    _name = 'doc.generator.markup'

    name = fields.Char('Name')
    key = fields.Char('Dynamic Value', compute='_compute_key', store=True)
    description = fields.Text('Description')
    text = fields.Char('Text')
    style = fields.Text('Style', default='{"color": "#FFFFFF"}')

    @api.model
    def _get_markup_data(self):
        markup_data = {}
        markups = self.search([])
        for markup in markups:
            style = json.loads(markup.style) or {}
            rich_text = RichText(markup.text, **style)
            markup_data[markup.name] = rich_text
        return markup_data

    @api.depends('name')
    def _compute_key(self):
        for record in self:
            record.key = '{{r %s}}' % record.name
