# -*- coding: utf-8 -*-
{
    'name': 'DPT Helpdesk Ticket',
    'version': '1.0',
    'summary': 'Manage Sale Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': '',
    'website': 'http://dpt.com',
    'depends': ['helpdesk', 'dpt_sale_management', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/helpdesk_ticket_sequence.xml',
        'views/helpdesk_ticket_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
}
