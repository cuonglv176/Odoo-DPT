# -*- coding: utf-8 -*-
{
    'name': 'Hierarchy Tree View',
    'version': '17.0',  # Cập nhật phiên bản cho Odoo 17
    'category': 'Extra Tools',
    'summary': 'Hierarchy Tree View',
    'author': 'Init Co. Ltd',
    'support': 'contact@init.vn',
    'website': 'https://init.vn/?utm_source=odoo-store&utm_medium=17&utm_campaign=hierarchy-tree-view',  # Cập nhật URL
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
    'assets': {
        'web.assets_backend': [
            'init_web_tree_view/static/src/scss/tree_view.scss',
            'init_web_tree_view/static/src/js/tree_controller.js',
            'init_web_tree_view/static/src/js/tree_model.js',
            'init_web_tree_view/static/src/js/tree_renderer.js',
            'init_web_tree_view/static/src/js/tree_view.js',
        ],
        'web.assets_web_dark': [
            'init_web_tree_view/static/src/scss/tree_view_dark.scss',
        ],
        'web.assets_qweb': [
            'init_web_tree_view/static/src/xml/web_tree_view.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
