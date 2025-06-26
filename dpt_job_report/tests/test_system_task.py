# -*- coding: utf-8 -*-

from odoo.tests import tagged
from .common import TestJobReportCommon
from datetime import datetime, timedelta


@tagged('post_install', '-at_install')
class TestSystemTask(TestJobReportCommon):
    """
    Feature: System Task Management
    As a CS employee
    I want to track system-generated tasks
    So that I can monitor work related to system events
    """

    def test_01_create_system_task(self):
        """
        Scenario: Create a system task
        Given I have a job report
        When I create a system task
        Then the task should be created with the correct values
        And the task should be in 'open' state
        """
        system_task = self.env['dpt.system.task'].create({
            'name': 'Test System Task',
            'report_id': self.job_report.id,
            'type': 'payment',
            'reference_model': 'sale.order',
            'reference_id': self.sale_order.id,
        })
        
        self.assertEqual(system_task.name, 'Test System Task', "Task name should be set correctly")
        self.assertEqual(system_task.report_id, self.job_report, "Task should be linked to the correct report")
        self.assertEqual(system_task.type, 'payment', "Task type should be set correctly")
        self.assertEqual(system_task.state, 'open', "New system task should be in 'open' state")
        self.assertEqual(system_task.reference_model, 'sale.order', "Reference model should be set correctly")
        self.assertEqual(system_task.reference_id, self.sale_order.id, "Reference ID should be set correctly")
        self.assertTrue(system_task.date_start, "Date start should be automatically set")
        self.assertFalse(system_task.date_end, "Date end should not be set for new task")

    def test_02_reference_name_computation(self):
        """
        Scenario: Reference name computation
        Given I have a system task with reference model and ID
        When the reference_name is computed
        Then it should display the name of the referenced record
        """
        system_task = self.env['dpt.system.task'].create({
            'name': 'Reference Name Test',
            'report_id': self.job_report.id,
            'type': 'payment',
            'reference_model': 'sale.order',
            'reference_id': self.sale_order.id,
        })
        
        self.assertEqual(system_task.reference_name, self.sale_order.name, 
                        "Reference name should display the name of the referenced sale order")

    def test_03_task_completion(self):
        """
        Scenario: Complete a system task
        Given I have an open system task
        When I mark the task as done
        Then the state should change to 'done'
        And the date_end should be set
        """
        system_task = self.env['dpt.system.task'].create({
            'name': 'Task to Complete',
            'report_id': self.job_report.id,
            'type': 'payment',
            'reference_model': 'sale.order',
            'reference_id': self.sale_order.id,
        })
        
        # Initial state
        self.assertEqual(system_task.state, 'open', "New system task should be in 'open' state")
        self.assertFalse(system_task.date_end, "Date end should not be set for new task")
        
        # Complete task
        system_task.action_done()
        self.assertEqual(system_task.state, 'done', "Task should be in 'done' state after completion")
        self.assertTrue(system_task.date_end, "Date end should be set when task is completed")

    def test_04_view_reference(self):
        """
        Scenario: View reference record
        Given I have a system task with a reference
        When I click to view the reference
        Then I should get an action to open the referenced record
        """
        system_task = self.env['dpt.system.task'].create({
            'name': 'View Reference Test',
            'report_id': self.job_report.id,
            'type': 'payment',
            'reference_model': 'sale.order',
            'reference_id': self.sale_order.id,
        })
        
        action = system_task.action_view_reference()
        self.assertEqual(action['res_model'], 'sale.order', "Action should open the correct model")
        self.assertEqual(action['res_id'], self.sale_order.id, "Action should open the correct record")
        self.assertEqual(action['type'], 'ir.actions.act_window', "Action should be of the correct type")

    def test_05_compute_system_tasks(self):
        """
        Scenario: Compute system tasks from job report
        Given I have a job report for a CS employee
        When I run the compute system tasks action
        Then system tasks should be created based on the employee's sales orders
        """
        # Create sale order with invoice status 'to invoice'
        sale_order_to_invoice = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'employee_cs': self.employee_cs.id,
            'date_order': self.today,
        })
        
        # Explicitly set invoice_status to 'to invoice'
        sale_order_to_invoice.write({'invoice_status': 'to invoice'})
        
        # Set department name to 'Customer Service' for the job report
        self.department_cs.write({'name': 'Customer Service'})
        
        # Run compute system tasks
        self.job_report.action_compute_system_tasks()
        
        # Check that system tasks were created for invoice
        invoice_tasks = self.env['dpt.system.task'].search([
            ('report_id', '=', self.job_report.id),
            ('type', '=', 'invoice'),
            ('reference_id', '=', sale_order_to_invoice.id)
        ])
        
        self.assertTrue(invoice_tasks, "Invoice task should be created for sale order with invoice status 'to invoice'")
        self.assertEqual(invoice_tasks[0].reference_model, 'sale.order', 
                        "Reference model should be set to sale.order")

    def test_06_task_type_selection(self):
        """
        Scenario: System task types
        Given I am creating system tasks
        When I set different task types
        Then the tasks should be created with the correct type values
        """
        # Test different task types
        task_types = ['payment', 'shipping', 'delivery', 'invoice']
        
        for task_type in task_types:
            system_task = self.env['dpt.system.task'].create({
                'name': f'Test {task_type.capitalize()} Task',
                'report_id': self.job_report.id,
                'type': task_type,
                'reference_model': 'sale.order',
                'reference_id': self.sale_order.id,
            })
            
            self.assertEqual(system_task.type, task_type, f"Task type should be set to {task_type}")
            self.assertTrue(system_task.name.startswith(f'Test {task_type.capitalize()}'), 
                          f"Task name should reflect the {task_type} type") 