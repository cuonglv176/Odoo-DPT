# -*- coding: utf-8 -*-
# Copyright (C) 2019-2021 Artem Shurshilov <shurshilov.a@yandex.ru>
# License OPL-1.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Custom report for odoo sale order and invoice",

    'summary': "Free module for beauti prepare data from docx_report_pro",

    'author': "EURO ODOO, Shurshilov Artem",
    'website': "https://eurodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '14.1.0.4',
    "license": "OPL-1",
    # 'price': 49,
    # 'currency': 'EUR',
    'images':[
        'static/description/template.png',
        'static/description/report_form.png',
        'static/description/result.png',
        'static/description/report_form.png',
    ],

    # any module necessary for this one to work correctly
    'depends': ['base','web','sale','account'],
    'installable': True,

}
