{
    'name': 'My HR',
    'depends': ['hr', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/attendance_report_view.xml',
        'views/emp_id_view.xml',
        'views/documents_view.xml',
        'views/contracts_view.xml',
        'views/hr_job_view.xml',
        'views/att_report_view.xml',
        'data/cron_data.xml'
        
    ],
    'price': 49.99,
    'currency': 'EUR'
}