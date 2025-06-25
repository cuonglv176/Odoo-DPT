# -*- coding: utf-8 -*-

from odoo.tests import tagged
from .common import TestJobReportCommon
from datetime import datetime, timedelta


@tagged('post_install', '-at_install')
class TestJobReport(TestJobReportCommon):
    """
    Feature: Job Report Management
    As a CS employee
    I want to track my tasks and performance
    So that I can manage my work efficiently
    """

    def test_01_job_report_creation(self):
        """
        Scenario: Create a new job report
        Given I am a CS employee
        When I create a new job report
        Then it should be in draft state
        And it should have a unique name
        And it should have the correct date range
        """
        self.assertEqual(self.job_report.state, 'draft', "New job report should be in draft state")
        self.assertNotEqual(self.job_report.name, 'New', "Job report should have a generated name")
        self.assertEqual(self.job_report.date_from, self.today, "Date from should be today")
        self.assertEqual(self.job_report.date_to, self.next_week, "Date to should be next week")
        self.assertEqual(self.job_report.employee_id, self.employee_cs, "Employee should be set correctly")

    def test_02_job_report_confirmation(self):
        """
        Scenario: Confirm a job report
        Given I have a draft job report
        When I confirm the job report
        Then the state should change to confirmed
        """
        self.job_report.action_confirm()
        self.assertEqual(self.job_report.state, 'confirmed', "Job report should be in confirmed state after confirmation")

    def test_03_job_report_reset_to_draft(self):
        """
        Scenario: Reset a confirmed job report to draft
        Given I have a confirmed job report
        When I reset the job report to draft
        Then the state should change to draft
        """
        self.job_report.action_confirm()
        self.job_report.action_draft()
        self.assertEqual(self.job_report.state, 'draft', "Job report should be in draft state after reset")

    def test_04_job_report_task_counts(self):
        """
        Scenario: Check task counts in job report
        Given I have a job report with tasks
        When I add job tasks and system tasks
        Then the task counts should be updated correctly
        """
        # Create job tasks
        self.env['dpt.job.task'].create([
            {
                'name': 'Test Job Task 1',
                'report_id': self.job_report.id,
                'priority': '1',
                'source': 'self',
            },
            {
                'name': 'Test Job Task 2',
                'report_id': self.job_report.id,
                'priority': '2',
                'source': 'self',
            }
        ])
        
        # Create system tasks
        self.env['dpt.system.task'].create([
            {
                'name': 'Test System Task',
                'report_id': self.job_report.id,
                'type': 'payment',
            }
        ])
        
        # Check counts
        self.job_report._compute_task_counts()
        self.assertEqual(self.job_report.job_task_count, 2, "Job task count should be 2")
        self.assertEqual(self.job_report.system_task_count, 1, "System task count should be 1")

    def test_05_job_report_performance_metrics(self):
        """
        Scenario: Job report performance metrics
        Given I have a job report with tasks
        When I calculate performance metrics
        Then the metrics should be calculated correctly
        """
        # Create tasks with different states and dates
        future_date = datetime.combine(self.today + timedelta(days=10), datetime.min.time())
        
        task1 = self.env['dpt.job.task'].create({
            'name': 'Task 1',
            'report_id': self.job_report.id,
            'priority': '2',
            'source': 'self',
            'deadline': future_date,
        })
        
        task2 = self.env['dpt.job.task'].create({
            'name': 'Task 2',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
            'deadline': future_date,
        })
        
        # Start and complete tasks
        task1.action_start()
        task1.date_start = datetime.now() - timedelta(hours=2)  # Started 2 hours ago
        task1.action_done()
        task1.date_end = datetime.now() - timedelta(hours=1)  # Finished 1 hour ago
        
        task2.action_start()
        task2.date_start = datetime.now() - timedelta(hours=3)  # Started 3 hours ago
        task2.action_done()
        task2.date_end = datetime.now() - timedelta(hours=1)  # Finished 1 hour ago
        
        # Calculate metrics
        self.job_report._compute_performance_metrics()
        
        # Check metrics
        self.assertEqual(self.job_report.completion_rate, 100.0, "Completion rate should be 100%")
        self.assertGreater(self.job_report.avg_processing_time, 0, "Average processing time should be positive")
        self.assertEqual(self.job_report.on_time_rate, 100.0, "On-time rate should be 100%")

    def test_06_action_view_tasks(self):
        """
        Scenario: View tasks from job report
        Given I have a job report with tasks
        When I click on the task count buttons
        Then I should see the correct action with the correct domain
        """
        # Create job task
        job_task = self.env['dpt.job.task'].create({
            'name': 'Test Job Task',
            'report_id': self.job_report.id,
            'priority': '1',
            'source': 'self',
        })
        
        # Create system task
        system_task = self.env['dpt.system.task'].create({
            'name': 'Test System Task',
            'report_id': self.job_report.id,
            'type': 'payment',
        })
        
        # Test action_view_job_tasks
        action = self.job_report.action_view_job_tasks()
        self.assertEqual(action['res_model'], 'dpt.job.task', "Action should open job tasks")
        self.assertEqual(action['domain'], [('report_id', '=', self.job_report.id)], 
                        "Domain should filter by report_id")
        
        # Test action_view_system_tasks
        action = self.job_report.action_view_system_tasks()
        self.assertEqual(action['res_model'], 'dpt.system.task', "Action should open system tasks")
        self.assertEqual(action['domain'], [('report_id', '=', self.job_report.id)], 
                        "Domain should filter by report_id") 