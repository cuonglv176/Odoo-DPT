{
    'name': 'DPT Customer Credit Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Advanced Customer Credit Management with Approval Workflow',
    'description': """
        Customer Credit Management Module for Odoo 17
        =============================================

        Features:
        * Credit limit management per customer
        * Payment terms tracking
        * Interest rate management for overdue amounts
        * Credit approval workflow
        * Automatic interest calculation
        * Credit history tracking
        * Sales order validation against credit limits
        * Comprehensive credit reports
    """,
    'author': 'IronX',
    'website': 'https://www.dpt.vn',
    'depends': [
        'base',
        'sale',
        'account',
        'approvals',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'data/approval_category_data.xml',
        'views/res_partner_views.xml',
        'views/credit_history_views.xml',
        'views/credit_config_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
        'reports/credit_report_views.xml',
        'wizards/credit_approval_wizard_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
