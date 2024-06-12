{
    'name': 'My Payroll',
    'depends': [
        'hr', 'hr_attendance', 'hr_holidays'
    ],
    'data': [
        'views/employee_view.xml',
        'views/att_view.xml',
        'views/timeoff_view.xml',
        # 'views/pl_view.xml',
        'views/penalities_view.xml',
        'security/ir.model.access.csv'
    ]
}