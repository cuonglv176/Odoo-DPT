# -*- coding: utf-8 -*-
{
    'name': 'DPT Service Management',
    'version': '17.0.1',
    'summary': 'Manage Services Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['base', 'init_web_tree_view', 'account', 'approvals', 'hr', 'sale', 'sales_team', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/service_sequence.xml',
        'data/approval_category_data.xml',  # Thêm dữ liệu cấu hình approval
        'views/service_view.xml',
        'views/service_combo_view.xml',
        'views/product.xml',
        'wizard/service_combo_reject_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
