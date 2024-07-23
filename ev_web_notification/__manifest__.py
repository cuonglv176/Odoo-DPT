# -*- coding: utf-8 -*-

{
    'name': 'Notification',
    'version': '1.0',
    'summary': 'Notification Website',
    'description': "",
    'depends': ['hr','bus', 'mail', 'ev_web_notify'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'ev_web_notification/static/src/**/*',
        ],
    },
}
