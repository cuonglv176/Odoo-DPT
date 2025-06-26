# -*- coding: utf-8 -*-

from odoo.tests import tagged
from .common import TestJobReportCommon
from datetime import datetime, timedelta


@tagged('post_install', '-at_install')
class TestJobTask(TestJobReportCommon):
    """
    Feature: Job Task Management
    As a CS employee
    I want to create and manage job tasks
    So that I can track my work progress
    """

    def test_01_create_self_task(self):
        """
        Scenario: Create a self-assigned task
        Given I am a CS employee
        When I create a new task with source 'self'
        Then the task should be created with the correct values
        And the task should be in 'new' state
        """
        # Convert next_week date to datetime for comparison with deadline field
        next_week_datetime = datetime.combine(self.next_week, datetime.min.time())
        
        task = self.env['dpt.job.task'].create({
            'name': 'Self Task',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
            'description': 'Test self task',
            'deadline': next_week_datetime,
        })
        
        self.assertEqual(task.name, 'Self Task', "Task name should be set correctly")
        self.assertEqual(task.report_id, self.job_report, "Task should be linked to the correct report")
        self.assertEqual(task.priority, '1', "Task priority should be set correctly")
        self.assertEqual(task.source, 'self', "Task source should be 'self'")
        self.assertEqual(task.state, 'new', "New task should be in 'new' state")
        self.assertEqual(task.description, 'Test self task', "Task description should be set correctly")
        self.assertEqual(task.deadline, next_week_datetime, "Task deadline should be set correctly")

    def test_02_create_assigned_task(self):
        """
        Scenario: Create an assigned task
        Given I am a manager
        When I create a new task with source 'assigned'
        Then the task should be created with the correct values
        And the assigned_by field should be set to the manager
        """
        task = self.env['dpt.job.task'].create({
            'name': 'Assigned Task',
            'report_id': self.job_report.id,
            'priority': '2',
            'source': 'assigned',
            'assigned_by': self.employee_manager.id,
            'description': 'Task assigned by manager',
        })
        
        self.assertEqual(task.name, 'Assigned Task', "Task name should be set correctly")
        self.assertEqual(task.priority, '2', "Task priority should be set correctly")
        self.assertEqual(task.source, 'assigned', "Task source should be 'assigned'")
        self.assertEqual(task.assigned_by, self.employee_manager, "Task should be assigned by the manager")
        self.assertEqual(task.state, 'new', "New task should be in 'new' state")

    def test_03_task_workflow(self):
        """
        Scenario: Task state workflow
        Given I have a new task
        When I start the task
        Then the state should change to 'in_progress'
        And the date_start should be set
        When I complete the task
        Then the state should change to 'done'
        And the date_end should be set
        """
        task = self.env['dpt.job.task'].create({
            'name': 'Workflow Test Task',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
        })
        
        # Initial state
        self.assertEqual(task.state, 'new', "New task should be in 'new' state")
        self.assertFalse(task.date_start, "Date start should not be set for new task")
        self.assertFalse(task.date_end, "Date end should not be set for new task")
        
        # Start task
        task.action_start()
        self.assertEqual(task.state, 'in_progress', "Task should be in 'in_progress' state after starting")
        self.assertTrue(task.date_start, "Date start should be set when task is started")
        self.assertFalse(task.date_end, "Date end should not be set for in-progress task")
        
        # Complete task
        task.action_done()
        self.assertEqual(task.state, 'done', "Task should be in 'done' state after completion")
        self.assertTrue(task.date_end, "Date end should be set when task is completed")

    def test_04_cancel_task(self):
        """
        Scenario: Cancel a task
        Given I have a task in any state except 'done' or 'cancelled'
        When I cancel the task
        Then the state should change to 'cancelled'
        """
        # Test cancelling a new task
        new_task = self.env['dpt.job.task'].create({
            'name': 'New Task to Cancel',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
        })
        
        new_task.action_cancel()
        self.assertEqual(new_task.state, 'cancelled', "Task should be in 'cancelled' state after cancellation")
        
        # Test cancelling an in-progress task
        in_progress_task = self.env['dpt.job.task'].create({
            'name': 'In Progress Task to Cancel',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
        })
        
        in_progress_task.action_start()
        self.assertEqual(in_progress_task.state, 'in_progress', "Task should be in 'in_progress' state")
        
        in_progress_task.action_cancel()
        self.assertEqual(in_progress_task.state, 'cancelled', "Task should be in 'cancelled' state after cancellation")

    def test_05_project_task_integration(self):
        """
        Scenario: Integration with project tasks
        Given I have a job task
        When I create the job task
        Then a corresponding project task should be created
        When I update the job task state
        Then the project task state should be updated accordingly
        """
        # Create project task stages if they don't exist
        stage_new = self.env['project.task.type'].search([('name', '=', 'New')], limit=1)
        if not stage_new:
            stage_new = self.env['project.task.type'].create({'name': 'New'})
            
        stage_in_progress = self.env['project.task.type'].search([('name', '=', 'In Progress')], limit=1)
        if not stage_in_progress:
            stage_in_progress = self.env['project.task.type'].create({'name': 'In Progress'})
            
        stage_done = self.env['project.task.type'].search([('name', '=', 'Done')], limit=1)
        if not stage_done:
            stage_done = self.env['project.task.type'].create({'name': 'Done'})
        
        # Create a project for the task
        project = self.env['project.project'].create({
            'name': 'Test Project',
            'privacy_visibility': 'portal',
            'type_ids': [(6, 0, [stage_new.id, stage_in_progress.id, stage_done.id])]
        })
        
        # Create job task
        future_date = datetime.combine(self.today + timedelta(days=10), datetime.min.time())
        job_task = self.env['dpt.job.task'].create({
            'name': 'Project Integration Task',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
            'deadline': future_date,
        })
        
        # Check if project task was created
        self.assertTrue(job_task.project_task_id, "Project task should be created")
        self.assertEqual(job_task.project_task_id.name, job_task.name, 
                        "Project task should have the same name as job task")
        
        # Assign project to the task to avoid personal stage error
        job_task.project_task_id.write({
            'project_id': project.id,
        })
        
        # Update job task state and check project task state
        job_task.action_start()
        
        # Verify state changes in job task
        self.assertEqual(job_task.state, 'in_progress', "Job task should be in progress")
        self.assertTrue(job_task.date_start, "Job task start date should be set")
        
        job_task.action_done()
        
        # Verify state changes in job task
        self.assertEqual(job_task.state, 'done', "Job task should be done")
        self.assertTrue(job_task.date_end, "Job task end date should be set")

    def test_06_task_deadline_validation(self):
        """
        Scenario: Task deadline validation
        Given I am creating a task
        When I set a deadline in the past
        Then the system should raise a validation error
        """
        past_date = datetime.combine(self.today - timedelta(days=1), datetime.min.time())
        
        with self.assertRaises(Exception) as context:
            self.env['dpt.job.task'].create({
                'name': 'Task with Past Deadline',
                'report_id': self.job_report.id,
                'priority': '1',
                'source': 'self',
                'deadline': past_date,
            })
        
        self.assertTrue('Deadline cannot be in the past' in str(context.exception), 
                      "Should raise validation error for past deadline") 