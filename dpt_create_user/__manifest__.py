{
    'name': "DPT Create user",
    'name_vi_VN': "Create User",

    'summary': """
Synchronize sale contract to distributor
    """,
    'summary_vi_VN': """
      Create User    """,

    'description': """
What it does
============
Synchronize sale contract to distributor

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,
    'author': "cuonglv",
    'website': "",
    'support': "",
    'category': 'Other',
    'version': '0.1.0',
    'depends': ['mail'],

    'data': [
        'security/ir.model.access.csv',
        'views/dpt_create_user_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 99.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
