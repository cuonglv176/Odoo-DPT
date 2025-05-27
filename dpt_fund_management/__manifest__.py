{
    'name': 'DPT Fund Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Fund Management System with Dashboard',
    'description': """
        Complete Fund Management System with:
        - Fund Accounts Management
        - Transactions Tracking
        - Fund Transfers
        - Exchange Rate Management
        - Audit Trail
        - Interactive Dashboard with Charts
    """,
    'author': 'Your Company',
    'depends': ['base', 'mail', 'account', 'web'],
    'external_dependencies': {
        'python': [
            'xlrd',  # Đọc file .xls
            'xlsxwriter',  # Tạo file .xlsx
            'openpyxl',  # Đọc file .xlsx (tùy chọn)
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'data/sequences.xml',
        'views/fund_account_views.xml',
        'views/fund_transaction_views.xml',
        'views/fund_transfer_views.xml',
        'views/exchange_rate_views.xml',
        'views/fund_audit_views.xml',
        'views/pending_transfer_views.xml',
        'views/fund_dashboard_views.xml',
        'views/bank_transaction_import_wizard_views.xml',
        'views/fund_transaction_export_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dpt_fund_management/static/src/css/fund_dashboard.css',
            'dpt_fund_management/static/src/js/fund_dashboard.js',
            'dpt_fund_management/static/src/xml/fund_dashboard_templates.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
