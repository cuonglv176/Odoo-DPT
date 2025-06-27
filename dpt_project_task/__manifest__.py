# -*- coding: utf-8 -*-
{
    'name': 'Báo cáo quản lý công việc',
    'version': '1.0',
    'summary': 'Báo cáo quản lý công việc dự án',
    'description': """
        Module báo cáo quản lý công việc dự án, thống kê task theo người dùng.
    """,
    'category': 'Project',
    'author': 'DPT',
    'depends': ['project'],
    'data': [
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/project_task_menu.xml',
        'data/project_data.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
} 