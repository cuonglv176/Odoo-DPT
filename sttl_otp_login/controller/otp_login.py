from random import choice
import string

from odoo.addons.web.controllers.home import Home, ensure_db
from odoo import http, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request


class OtpLoginHome(Home):
    
    @http.route(website=True)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        qcontext = request.params.copy()

        if request.httprequest.method == 'GET':

            if "otp_login" and "otp" in kw:
                if kw["otp_login"] and kw["otp"]:
                    return request.render("sttl_otp_login.custom_login_template", {'otp': True, 'otp_login': True})
            if "otp_login" in kw: #checks if the keyword "otp_login" exists in the dict "kw".
                if kw["otp_login"]: #checks if the value of "otp_login" is true.
                    return request.render("sttl_otp_login.custom_login_template", {'otp_login': True})
            else:
                return super(OtpLoginHome, self).web_login(redirect, **kw)
        else:
            if kw.get('login'):
                request.params['login'] = kw.get('login').strip()
            if kw.get('password'):
                request.params['password'] = kw.get('password').strip()
            return super(OtpLoginHome, self).web_login(redirect, **kw)

        return request.render("sttl_otp_login.custom_login_template", {})

    @http.route('/web/otp/login', type='http', auth='public', website=True, csrf=False)
    def web_otp_login(self, **kw):
        qcontext = request.params.copy()
        email = str(qcontext.get('login'))
        user_id = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)

        if user_id:
            OTP = self.generate_otp(4)
            vals = {
                'otp': OTP,
                'email': email
            }
            mail_body = """\
                            <html>
                                <body>
                                    <p>
                                        Dear <b>%s</b>,
                                            <br>
                                            <p> 
                                                To complete the verification process for your Odoo account, 
                                                <br>Please use the following One-Time Password (OTP): <b>%s</b>
                                            </p>
                                        Thanks & Regards.
                                    </p>
                                </body>
                            </html>
                        """ % (user_id.name, OTP)
            mail = request.env['mail.mail'].sudo().create({
                'subject': _('Verify Your Odoo Account - OTP Required'),
                'email_from': user_id.company_id.email,
                'author_id': user_id.partner_id.id,
                'email_to': email,
                'body_html': mail_body,
            })
            mail.send()
            response = request.render("sttl_otp_login.custom_login_template", {'otp': True, 'otp_login': True,
                                                                               'login': qcontext["login"],
                                                                               'otp_no': OTP})
            request.env['otp.verification'].sudo().create(vals)
            return response

        else:
            response = request.render("sttl_otp_login.custom_login_template", {'otp': False, 'otp_login': True,
                                                                               'login_error': True})
            return response

    @http.route('/web/otp/verify', type='http', auth='public', website=True, csrf=False)
    def web_otp_verify(self, *args, **kw):
        qcontext = request.params.copy()
        email = str(kw.get('login'))
        res_id = request.env['otp.verification'].search([('email', '=', email)], order="create_date desc", limit=1)

        try:
            otp = str(kw.get('otp'))
            otp_no = res_id.otp
            if otp_no == otp:
                res_id.state = 'verified'
                user_id = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                request.env.cr.execute(
                    "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                    [user_id.id]
                )
                hashed = request.env.cr.fetchone()[0]
                qcontext.update({'login': user_id.sudo().login,
                                 'name': user_id.sudo().partner_id.name,
                                 'password': hashed + 'mobile_otp_login'})
                request.params.update(qcontext)
                return self.web_login(*args, **kw)
            else:
                res_id.state = 'rejected'
                response = request.render('sttl_otp_login.custom_login_template', {'otp': True, 'otp_login': True,
                                                                                   'login': email})
                return response
        except UserError as e:
            qcontext['error'] = e.name or e.value

        response = request.render('sttl_otp_login.custom_login_template', {'otp': True, 'otp_login': True,
                                                                           'login': email})
        return response

    def generate_otp(self, number_of_digits):
        otp = ''.join(choice(string.digits) for _ in range(number_of_digits))
        return otp
