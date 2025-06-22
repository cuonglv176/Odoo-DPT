{
    'name': 'DPT Sale Service Discount Management',
    'version': '17.0.1.0.0',
    'category': 'Sales/Services',
    'summary': 'Advanced discount management for DPT service business with Odoo approval workflow',
    'description': """
        Comprehensive discount management system for DPT service business:
        - Service-specific discount policies with Odoo approval workflow
        - Service combo discount management
        - Integration with dpt.sale.service.management
        - Support for dpt.sale.order.service.combo
        - Multi-level approval using Odoo's approval system
        - Detailed discount tracking and reporting
    """,
    'author': 'IronX',
    'website': 'https://www.dpt.com',
    'depends': [
        'base',
        'sale',
        'product',
        'account',
        'mail',
        'approvals',
        'dpt_sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/discount_sequence.xml',
        'data/approval_category_data.xml',
        'data/discount_data.xml',
        'views/service_discount_policy_views.xml',
        'views/service_combo_discount_views.xml',
        'views/sale_order_discount_views.xml',
        'views/discount_menu.xml',
        'wizard/service_discount_wizard.xml',
        # 'wizard/combo_discount_wizard.xml'
    ],
    'demo': [
        # 'demo/service_discount_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
