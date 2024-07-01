from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServerActions(models.Model):
    _inherit = 'ir.actions.server'

    def _run_action_mail_post_multi(self, eval_context=None):
        # TDE CLEANME: when going to new api with server action, remove action
        if not self.template_id or (
                not self._context.get('active_ids') and not self._context.get('active_id')) or self._is_recompute():
            return False
        res_ids = self._context.get('active_ids', [self._context.get('active_id')])

        # Clean context from default_type to avoid making attachment
        # with wrong values in subsequent operations
        cleaned_ctx = dict(self.env.context)
        cleaned_ctx.pop('default_type', None)
        cleaned_ctx.pop('default_parent_id', None)
        cleaned_ctx['mail_create_nosubscribe'] = True  # do not subscribe random people to records
        cleaned_ctx['mail_post_autofollow'] = self.mail_post_autofollow
        email_to = ','.join([u.email for u in self.base_automation_id.partner_ids])
        force_send = True if self.base_automation_id else False
        if self.mail_post_method in ('comment', 'note'):
            records = self.env[self.model_name].with_context(cleaned_ctx).browse(res_ids)
            if self.mail_post_method == 'comment':
                subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
            else:
                subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
            records.message_post_with_source(
                self.template_id,
                subtype_id=subtype_id,
            )
        else:
            template = self.template_id.with_context(cleaned_ctx)
            for res_id in res_ids:
                template.send_mail(
                    res_id,
                    force_send=force_send,
                    raise_exception=False,
                    email_values={
                        'email_to': email_to,
                        'recipient_ids': self.base_automation_id.partner_ids
                    }
                )
        return False
