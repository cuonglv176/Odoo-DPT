from odoo import _, api, fields, models, tools, Command
import logging
from odoo.tools import is_html_empty


_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = "mail.template"


    def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None,
                  email_layout_xmlid=False):
        """ Generates a new mail.mail. Template is rendered on record given by
        res_id and model coming from template.

        :param int res_id: id of the record to render the template
        :param bool force_send: send email immediately; otherwise use the mail
            queue (recommended);
        :param dict email_values: update generated mail with those values to further
            customize the mail;
        :param str email_layout_xmlid: optional notification layout to encapsulate the
            generated email;
        :returns: id of the mail.mail that was created """

        # Grant access to send_mail only if access to related document
        self.ensure_one()
        self._send_check_access([res_id])

        Attachment = self.env['ir.attachment']  # TDE FIXME: should remove default_type from context

        # create a mail_mail based on values, without attachments
        values = self._generate_template(
            [res_id],
            ('attachment_ids',
             'auto_delete',
             'body_html',
             'email_cc',
             'email_from',
             'email_to',
             'mail_server_id',
             'model',
             'partner_to',
             'reply_to',
             'report_template_ids',
             'res_id',
             'scheduled_date',
             'subject',
            )
        )[res_id]
        values['recipient_ids'] = [Command.link(pid) for pid in values.get('partner_ids', list())]
        if email_values.get('recipient_ids'):
            values['recipient_ids'] = [Command.link(pid) for pid in email_values.get('recipient_ids', list())]
        values['attachment_ids'] = [Command.link(aid) for aid in values.get('attachment_ids', list())]
        values.update(email_values or {})
        attachment_ids = values.pop('attachment_ids', [])
        attachments = values.pop('attachments', [])
        # add a protection against void email_from
        if 'email_from' in values and not values.get('email_from'):
            values.pop('email_from')
        # encapsulate body
        email_layout_xmlid = email_layout_xmlid or self.email_layout_xmlid
        if email_layout_xmlid and values['body_html']:
            record = self.env[self.model].browse(res_id)
            model = self.env['ir.model']._get(record._name)

            if self.lang:
                lang = self._render_lang([res_id])[res_id]
                model = model.with_context(lang=lang)

            template_ctx = {
                # message
                'message': self.env['mail.message'].sudo().new(dict(body=values['body_html'], record_name=record.display_name)),
                'subtype': self.env['mail.message.subtype'].sudo(),
                # record
                'model_description': model.display_name,
                'record': record,
                'record_name': False,
                'subtitles': False,
                # user / environment
                'company': 'company_id' in record and record['company_id'] or self.env.company,
                'email_add_signature': False,
                'signature': '',
                'website_url': '',
                # tools
                'is_html_empty': is_html_empty,
            }
            body = model.env['ir.qweb']._render(email_layout_xmlid, template_ctx, minimal_qcontext=True, raise_if_not_found=False)
            if not body:
                _logger.warning(
                    'QWeb template %s not found when sending template %s. Sending without layout.',
                    email_layout_xmlid,
                    self.name
                )

            values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
        if 'body_html' in values:
            values['body'] = values['body_html']

        mail = self.env['mail.mail'].sudo().create(values)

        # manage attachments
        for attachment in attachments:
            attachment_data = {
                'name': attachment[0],
                'datas': attachment[1],
                'type': 'binary',
                'res_model': 'mail.message',
                'res_id': mail.mail_message_id.id,
            }
            attachment_ids.append((4, Attachment.create(attachment_data).id))
        if attachment_ids:
            mail.write({'attachment_ids': attachment_ids})

        if force_send:
            mail.send(raise_exception=raise_exception)
        return mail.id  # TDE CLEANME: return mail + api.returns ?