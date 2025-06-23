{
    'name': 'Asset Department Extension',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Add department and employee fields to assets',
    'description': """
    """,
    'depends': ['account_asset', 'hr'],
    'data': [
        'views/account_asset_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
