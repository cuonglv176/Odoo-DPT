# -*- coding: utf-8 -*-
{
    'name': "VTG In-Stock Update",

    'summary': """Update quantity and price for product""",

    'author': "TuUH",

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_update_popup.xml',
    ],
}
