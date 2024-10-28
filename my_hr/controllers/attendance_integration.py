from odoo import http, tools
from odoo.http import request
from datetime import datetime, timedelta
import json
import requests


class att_emp(http.Controller):

    @http.route('/serach_emp', auth='public', methods=['POST'], csrf=False)
    def search_emp(self, **kwargs):

        request_data = json.loads(http.request.httprequest.data)

        id = request_data.get('machine_id')

        model = http.request.env['hr.employee'].sudo()

        employee_id = model.search([('machine_id', '=', int(id))], limit=1).id

        if employee_id:

            return json.dumps({
                'emp_id': employee_id
            })
            
        else:
            return json.dumps({
                'emp_id': False
            })


    @http.route('/insert_att', auth='public', methods=['POST'], csrf=False)
    def insert_att(self, **kwargs):

        try:

            request_data = json.loads(http.request.httprequest.data)

            employee_id = request_data.get('employee_id')
            check_in_str  = request_data.get('check_in')
            check_out_str  = request_data.get('check_out')

            check_in_dt = datetime.strptime(check_in_str, '%Y-%m-%d %H:%M:%S')
            check_out_dt = datetime.strptime(check_out_str, '%Y-%m-%d %H:%M:%S')

            check_in = check_in_dt - timedelta(hours=3)
            check_out = check_out_dt - timedelta(hours=3)

            model = http.request.env['hr.attendance'].sudo()

            new_attendance_record = model.create({
                'employee_id': int(employee_id),
                'check_in': check_in,
                'check_out': check_out,
                'remote': False
            })   

            return json.dumps({
                'result': 'success'
            })
        except Exception as e:
            return json.dumps({
                'result': str(e)
            })

