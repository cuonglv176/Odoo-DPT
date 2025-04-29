from random import choice
import string

from odoo.addons.web.controllers.home import Home, ensure_db
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError


class OtpSignupHome(Home):

    @http.route(website=True)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        return super(OtpSignupHome, self).web_auth_signup(*args, **kw)

    @http.route('/web/signup/otp', type='http', auth='public', website=True, sitemap=False)
    def web_signup_otp(self, **kw):
        qcontext = request.params.copy()
        OTP = self.generate_otp(4)
        if "login" in qcontext and qcontext["login"] and qcontext["password"] == qcontext["confirm_password"]:
            user_id = request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))])
            if user_id:
                qcontext["error"] = _("Another user is already registered using this email address.")
                response = request.render('sttl_otp_login.custom_otp_signup', qcontext)
                return response
            else:
                email = str(qcontext.get('login'))
                name = str(qcontext.get('name'))
                vals = {
                    'otp': OTP,
                    'email': email
                }
                email_from = request.env.company.email
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
                            """ % (name, OTP)
                mail = request.env['mail.mail'].sudo().create({
                    'subject': _('Verify Your Odoo Account - OTP Required'),
                    'email_from': email_from,
                    'email_to': email,
                    'body_html': mail_body,
                })
                mail.send()
                response = request.render('sttl_otp_login.custom_otp_signup', {'otp': True, 'otp_login': True,
                                                                               'login': qcontext["login"],
                                                                               'otp_no': OTP,
                                                                               'name': qcontext["name"],
                                                                               'password': qcontext["password"],
                                                                               'confirm_password': qcontext[
                                                                                   "confirm_password"]})
                res = request.env['otp.verification'].sudo().create(vals)
                return response
        else:
            qcontext["error"] = _("Passwords do not match, please retype them.")
            response = request.render('sttl_otp_login.custom_otp_signup', qcontext)
            return response

    @http.route('/web/signup/otp/verify', type='http', auth='public', website=True, sitemap=False)
    def web_otp_signup_verify(self, *args, **kw):
        qcontext = request.params.copy()
        email = str(kw.get('login'))
        res_id = request.env['otp.verification'].search([('email', '=', email)], order="create_date desc", limit=1)
        name = str(kw.get('name'))
        password = str(qcontext.get('password'))
        confirm_password = str(qcontext.get('confirm_password'))

        try:
            otp = str(kw.get('otp'))
            otp_no = res_id.otp
            if otp_no == otp:
                res_id.state = 'verified'
                return self.web_auth_signup(*args, **kw)
            else:
                res_id.state = 'rejected'
                response = request.render('sttl_otp_login.custom_otp_signup', {'otp': True, 'otp_login': True,
                                                                               'login': email, 'name': name,
                                                                               'password': password,
                                                                               'confirm_password': confirm_password})
                return response
        except UserError as e:
            qcontext['error'] = e.name or e.value

        response = request.render('sttl_otp_login.custom_otp_signup', {'otp': True, 'otp_login': True,
                                                                       'login': email, 'name': name,
                                                                       'password': password,
                                                                       'confirm_password': confirm_password
                                                                       })
        return response

    def generate_otp(self, number_of_digits):
        otp = ''.join(choice(string.digits) for _ in range(number_of_digits))
        return otp
