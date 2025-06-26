# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta


class TestJobReportCommon(TransactionCase):
    """Base class for all job report tests that provides common setup"""

    @classmethod
    def setUpClass(cls):
        super(TestJobReportCommon, cls).setUpClass()
        
        # Create test users and employees
        cls.user_cs = cls.env['res.users'].create({
            'name': 'CS User',
            'login': 'cs_user',
            'email': 'cs_user@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })
        
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Manager User',
            'login': 'manager_user',
            'email': 'manager_user@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })
        
        cls.department_cs = cls.env['hr.department'].create({
            'name': 'Customer Service'
        })
        
        cls.job_cs = cls.env['hr.job'].create({
            'name': 'CS Officer'
        })
        
        cls.employee_cs = cls.env['hr.employee'].create({
            'name': 'CS Employee',
            'user_id': cls.user_cs.id,
            'department_id': cls.department_cs.id,
            'job_id': cls.job_cs.id
        })
        
        cls.employee_manager = cls.env['hr.employee'].create({
            'name': 'Manager',
            'user_id': cls.user_manager.id,
            'department_id': cls.department_cs.id,
        })
        
        # Create a job report
        cls.today = datetime.today().date()
        cls.next_week = cls.today + timedelta(days=7)
        
        cls.job_report = cls.env['dpt.job.report'].create({
            'employee_id': cls.employee_cs.id,
            'date_from': cls.today,
            'date_to': cls.next_week,
        })
        
        # Create a sale order for reference
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
        })
        
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'employee_cs': cls.employee_cs.id,
        })
        
        # Create project for task integration
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
            'privacy_visibility': 'employees',
        }) 