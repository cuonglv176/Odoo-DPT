from odoo import models, fields, api, _
from odoo.exceptions import UserError


class dptResellerUser(models.Model):
    _name = 'dpt.reseller.users'
    _description = 'Reseller users'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    name = fields.Char(string='Full Name')
    login = fields.Char(string='Account User')
    password = fields.Char(string='Password')
    phone = fields.Char(string='Phone')
    user_id = fields.Many2one('res.users', string='User')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Created'),
        ('close', 'Closed')
    ], default='draft', string='State')
    user_template_id = fields.Many2one('dpt.reseller.users.template', string='Account type', required=True)
    state_users = fields.Selection([
        ('new', 'New'),
        ('active', 'Actived')
    ], related='user_id.state', default='new', string='Status User')

    def action_reset_password(self):
        self.sudo().user_id.action_reset_password()

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.name = self.employee_id.name
            self.login = self.employee_id.work_email
            self.phone = self.employee_id.mobile_phone

    def action_create_user(self):
        vals = {
            "name": self.name,
            "login": self.login,
            "password": self.password or 'dpt@123',
            "active": True,
            # "x_create_user_id": self.id,
            # "x_user_template_id": self.user_template_id.id,
        }
        new_user_id = self.sudo().user_template_id.user_id.copy(default=vals)
        self.user_id = new_user_id
        self.employee_id.user_id = new_user_id
        self.sudo().user_id.partner_id.phone = self.phone
        self.sudo().user_id.partner_id.email = self.login
        self.sudo().user_id.action_reset_password()
        self.state = 'done'

    def write(self, vals):
        for user_id in self:
            user_id = user_id.sudo()  # fix lõi thiếu quyền thao tác user trưởng phòng
            login_old = user_id.login
            res = super(dptResellerUser, self).write(vals)
            login_new = user_id.login
            vals = {
                "name": user_id.name,
                "login": user_id.login,
            }
            user_id.user_id.write(vals)
            if login_old != login_new:
                user_id.user_id.action_reset_password()
            # user_id.user_id.user_template_id = user_id.user_template_id

            # que = """SELECT id user_id FROM res_users WHERE id not in(
            #          SELECT res_users_id FROM res_partner_res_users_rel WHERE res_partner_id = %s) and active=TRUE"""
            # self.env.cr.execute(que, (int(user_id.user_id.partner_id.id),))
            # res1 = self.env.cr.fetchall()
            # if res1:
            #     for r in res1:
            # que_3 = """INSERT INTO res_partner_res_users_rel(res_users_id,res_partner_id)
            #             SELECT id,%s FROM res_users WHERE id not in(
            #             SELECT res_users_id FROM res_partner_res_users_rel WHERE res_partner_id = %s)
            #             """
            # self.env.cr.execute(que_3, (int(user_id.user_id.partner_id.id), int(user_id.user_id.partner_id.id)))
            return res

    def action_close_user(self):
        self.sudo().user_id.active = False
        self.state = 'close'

    def action_open_user(self):
        self.sudo().user_id.active = True
        self.state = 'done'


class dptResellerUserTemplate(models.Model):
    _name = 'dpt.reseller.users.template'

    name = fields.Char(string='Account Type', required=True)
    user_id = fields.Many2one('res.users', string='User Template', required=True)
