from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        res = super(AccountPayment, self).create(vals)
        if self.move_id:
            self.sale_id = self.move_id.sale_id
        return res

    def write(self, vals):
        if 'move_id' in vals:
            move_id = self.env['account.move'].browse(vals.get('move_id'))
            if move_id.sale_id:
                vals.update(
                    {
                        'sale_id': move_id.sale_id.id
                    }
                )
        res = super(AccountPayment, self).write(vals)
        return res
