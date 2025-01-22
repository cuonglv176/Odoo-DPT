# __manifest__.py
{
    'name': 'DPT Currency Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Currency',
    'summary': 'Enhanced Currency Management System',
    'description': """
        Module for managing currencies and exchange rates with:
        - Dashboard view
        - Easy rate updates
        - Historical tracking
        - Rate change notifications
    """,
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/currency_rate_view.xml',
        'views/currency_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
