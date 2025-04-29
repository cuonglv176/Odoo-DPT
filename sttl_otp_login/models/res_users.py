from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
import logging
import pytz

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'

        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
                    if not user:
                        raise AccessDenied()
                    user = user.with_user(user)
                    self.env.cr.execute(
                        "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                        [user.id]
                    )
                    hashed = self.env.cr.fetchone()[0]
                    if not password == hashed + 'mobile_otp_login':
                        user._check_credentials(password, user_agent_env)

                    tz = request.httprequest.cookies.get('tz') if request else None
                    if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                        # first login or missing tz -> set tz to browser tz
                        user.tz = tz
                    user._update_last_login()

        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
            raise

        _logger.info("Login successful for db:%s login:%s from %s", db, login, ip)

        return user.id
