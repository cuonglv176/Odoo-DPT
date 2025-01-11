# -*- coding: utf-8 -*-
{
    'name': "DPT Security",

    'summary': """
        Security""",

    'description': """
        Security
    """,

    'author': "CuongLV",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm','sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'security/rule_security.xml',
    ],
}
