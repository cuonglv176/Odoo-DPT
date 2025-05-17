from odoo import models, fields, api, _


class IrActionReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_rendering_context(self, report, docids, data):
        res = super(IrActionReport, self)._get_rendering_context(report, docids, data)
        model = data.get('model', False)
        if model:
            res.update({
                'doc_model': model,
                'docs': self.env[model].browse(docids),
            })
        return res
