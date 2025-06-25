# -*- coding: utf-8 -*-
{
    'name': "Job Report Management",
    'summary': """
        Module quản lý và theo dõi công việc theo job
    """,
    'description': """
        Module báo cáo theo dõi công việc theo job cho phép:
        - Theo dõi công việc từ nhiều nguồn (đơn hàng, phiếu vận chuyển, tasks...)
        - Phân loại công việc theo job position
        - Tạo và giao việc giữa quản lý và nhân viên
        - Hiển thị dashboard hiệu suất
        - Báo cáo công việc hàng tháng
        - Đánh giá kết quả công việc
        - Tự đánh giá và nhận xét của nhân viên
        
        Giai đoạn 1: Triển khai cho phòng CS
        Giai đoạn 2: Mở rộng cho tất cả phòng ban
    """,
    'author': "DPT",
    'website': "https://dpt.com",
    'category': 'Human Resources/Job Report',
    'version': '0.1',
    'depends': [
        'base', 
        'sale', 
        'purchase', 
        'project', 
        'helpdesk', 
        'hr',
        'dpt_export_import', 
        'dpt_shipping', 
        'stock'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/ir_cron.xml',
        'wizard/evaluate_views.xml',
        'wizard/self_evaluate_views.xml',
        'views/job_task_views.xml',
        'views/system_task_views.xml',
        'views/job_report_views.xml',
        'views/hr_employee_views.xml',
        'views/assign_task_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
} 