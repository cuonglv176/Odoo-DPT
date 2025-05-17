# -*- coding: utf-8 -*-
# Copyright (C) 2019-2022 Artem Shurshilov <shurshilov.a@yandex.ru>
# License OPL-1.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "docx report PROFESSIONAL version template ms populating (WORD,LIBRE,OPENOFFICE)",

    'summary': " \
Do report template in docx and see result in docx with odoo data \
Populating MS Word Templates with Python microsoft libreoffice openofiice \
doc docx template doc templates docx template docx ms docx microsoft word \
Template Report DOCX Is Easy an elegant and scalable solution to \
design reports using Microsoft Office Export data all objects odoo to Microsoft Office \
output files docx pdf docx to pdf docx to odt docx pdf docx odt \
reports pdf reports docx to pdf report docx to pdf docx to odt report \
docx to pdf report dcox to docx report docx to pdf reports \
output docx output docx report output \
fish docx fish docx to pdf jinja docx jinja2 \
",

    'author': "EURO ODOO, Shurshilov Artem",
    'website': "https://eurodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical Settings',
    "license": "OPL-1",
    'price': 49,
    'currency': 'EUR',
    'images': [
        'static/description/template.png',
        'static/description/report_form.png',
        'static/description/result.png',
        'static/description/report_form.png',
    ],

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],
    # "external_dependencies": {"python": ['docxtpl'], "bin": ['libreoffice']},
    "external_dependencies": {"python": ['docxtpl==0.11.3']},
    'installable': True,

    # always loaded
    'data': [
        'views/views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'docx_report_pro/static/**/*',
        ],
    },

}
