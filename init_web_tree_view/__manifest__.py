# -*- coding: utf-8 -*-
{
    'name': 'Hierarchy Tree View',
    'version': '16.0.1.0.5',
    'category': 'Extra Tools',
    'summary': 'Hierarchy Tree View',
    'author': 'Init Co. Ltd',
    'support': 'contact@init.vn',
    'website': 'https://init.vn/?utm_source=odoo-store&utm_medium=15&utm_campaign=hierarchy-tree-view',
    'license': 'LGPL-3',
    'price': '29',
    'currency': 'USD',
    'description': """Hierarchy Tree View""",
    'depends': [
        'web',
    ],
    'data': [
        # data

        # wizard

        # view

        # wizard

        # report

        # menu

        # security
    ],
    'qweb': [],
    'demo': [],
    'test': [],
    'assets': {
        'web.assets_backend': [
            'init_web_tree_view/static/src/scss/tree_view.scss',
            'init_web_tree_view/static/src/js/tree_controller.js',
            'init_web_tree_view/static/src/js/tree_model.js',
            'init_web_tree_view/static/src/js/tree_renderer.js',
            'init_web_tree_view/static/src/js/tree_view.js',
            'init_web_tree_view/static/src/xml/web_tree_view.xml',

        ],

    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
