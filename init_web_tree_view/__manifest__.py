# -*- coding: utf-8 -*-
{
    'name': 'Hierarchy Tree View',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Hierarchy Tree View',
    'author': 'Init Co. Ltd',
    'support': 'contact@init.vn',
    'website': 'https://init.vn/?utm_source=odoo-store&utm_medium=17&utm_campaign=hierarchy-tree-view',
    'license': 'LGPL-3',
    'price': '35',
    'currency': 'USD',
    'description': """Hierarchy Tree View""",
    'depends': [
        'web',
        'sale',
    ],
    'data': [
        # data

        # wizard

        # view
        # 'views/dev_sample/sale_order_view.xml',

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
            'init_web_tree_view/static/src/js/tree_controller.js',
            'init_web_tree_view/static/src/js/tree_controller.xml',

            'init_web_tree_view/static/src/js/tree_renderer.js',
            'init_web_tree_view/static/src/js/tree_renderer.xml',

            'init_web_tree_view/static/src/js/init_tree_arch_parse.js',
            'init_web_tree_view/static/src/js/init_tree_model.js',
            'init_web_tree_view/static/src/js/tree_view.js',
            'init_web_tree_view/static/src/scss/tree_view.scss',
        ],

    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
