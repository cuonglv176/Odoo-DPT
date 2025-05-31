from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class HrEmployee(models.Model):
   _inherit = 'hr.employee'


   code = fields.Char('Code')
   dpt_level = fields.Selection([
       ('l1', 'L1'),
       ('l2', 'L2'),
       ('l3', 'L3'),
       ('l4', 'L4'),
       ('l5', 'L5')
   ], default='l1', string='Cấp bậc')
   parent_department_id = fields.Many2one('hr.department', string='Phòng')
   center_id = fields.Many2one('hr.department', string='Trung tâm')
   bod_code = fields.Char(string='Mã BOD')
   company_join_date = fields.Date(string='Thời gian vào công ty')
   legal_entity = fields.Selection([
       ('dpt', 'DPT'),
       ('ltv', 'LTV')
   ], string='Pháp nhân', default='dpt')
   has_children = fields.Selection([
       ('yes', 'Đã có con'),
       ('no', 'Chưa có con')
   ], string='Tình trạng con cái', default='no')
   identification_date = fields.Date('Ngày cấp CCCD', groups="hr.group_hr_user", tracking=True)
   place_of_identification = fields.Char('Nơi cấp CCCD', groups="hr.group_hr_user", tracking=True)
   @api.onchange('job_id')
   def onchange_job_id(self):
       self.department_id = self.job_id.department_id
       self.parent_department_id = self.job_id.parent_department_id
       self.center_id = self.job_id.center_id
       self.bod_code = self.job_id.bod_code


class HrEmployeePublic(models.Model):
   _inherit = 'hr.employee.public'

   code = fields.Char('Code', related='employee_id.code', compute_sudo=True)
   dpt_level = fields.Selection([
       ('l1', 'L1'),
       ('l2', 'L2'),
       ('l3', 'L3'),
       ('l4', 'L4'),
       ('l5', 'L5')
   ], default='l1', string='Cấp bậc', related='employee_id.dpt_level', compute_sudo=True)
   parent_department_id = fields.Many2one('hr.department', string='Phòng', related='employee_id.parent_department_id', compute_sudo=True)
   center_id = fields.Many2one('hr.department',string='Trung tâm', related='employee_id.center_id', compute_sudo=True)
   bod_code = fields.Char(string='Mã BOD', related='employee_id.bod_code', compute_sudo=True)
   
   company_join_date = fields.Date(string='Thời gian vào công ty', related='employee_id.company_join_date', compute_sudo=True)
   legal_entity = fields.Selection([
       ('dpt', 'DPT'),
       ('ltv', 'LTV')
   ], string='Pháp nhân', related='employee_id.legal_entity', compute_sudo=True)
   has_children = fields.Selection([
       ('yes', 'Đã có con'),
       ('no', 'Chưa có con')
   ], string='Tình trạng con cái', related='employee_id.has_children', compute_sudo=True)
   identification_date = fields.Date('Ngày cấp CCCD', related='employee_id.identification_date', compute_sudo=True)
   place_of_identification = fields.Char('Nơi cấp CCCD', related='employee_id.place_of_identification', compute_sudo=True)

