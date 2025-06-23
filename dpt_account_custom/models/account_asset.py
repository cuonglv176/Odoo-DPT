from odoo import fields, models

class AccountAsset(models.Model):
    _inherit = 'account.asset'
    
    employee_id = fields.Many2one('hr.employee', string='Nhân viên')
    department_id = fields.Many2one('hr.department', string='Bộ phận')