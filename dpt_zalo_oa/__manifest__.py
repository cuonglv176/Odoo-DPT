# -*- coding: utf-8 -*-
{
    'name': 'DPT Zalo OA',
    'version': '1.0',
    'summary': 'Manage Zalo Oa',
    'category': 'hr',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['base', 'base_automation', 'base_setup', 'ev_web_notify'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/base_automation_view.xml',
        'views/dpt_zalo_template_views.xml',
        'views/zalo_menu.xml',
        'data/ir_cron_data.xml',
    ],
}
