from odoo import http, tools
from odoo.http import request
import json
from datetime import datetime, timedelta
import time
import requests



url = "http://196.221.197.20/ISAPI/AccessControl/AcsEvent?format=json"
auth = requests.auth.HTTPDigestAuth('admin', 'n1234567')

class SPInt(http.Controller):
 
    @http.route('/insert/att/record/today', auth='user', methods=['POST'], csrf=False)
    def approval(self, **kwargs):
        try:

            IDs = []
            TIMES = []

            current_time = datetime.now()
            new_start_time = current_time - timedelta(hours=23)

            # start_time = new_start_time.strftime("%Y-%m-%dT%H:%M:%S+02:00")
            start_time = "2024-07-21T00:00:00+02:00"
            # end_time = current_time.strftime("%Y-%m-%dT%H:%M:%S+02:00")
            end_time = "2024-07-21T22:59:59+02:00"

            data = {
                "AcsEventCond": {
                    "searchID": "laff0562-8328-42ce-Sec7-dcb8d3b7de35",
                    "searchResultPosition": 0,
                    "maxResults": 1000,
                    "major": 0,
                    "minor": 0,
                    "startTime": start_time,
                    "endTime": end_time
                }
            }

            response = requests.post(url, auth=auth, data=json.dumps(data))
            total_matches_no = response.json()['AcsEvent']['totalMatches']

            for j in range((total_matches_no//30)+1):


                query = {
                    "AcsEventCond":{"searchID":f"laff0362-9328-42ce-Sec7-dcb7d3b8de3{j}","searchResultPosition":30*j,
                                    "maxResults":1000,"major":0,"minor":75,"startTime":start_time,
                                    "endTime":end_time}
                    } 
                
        
                response = requests.post(url, auth=auth, data=json.dumps(query))
            

                if 'InfoList' in list(response.json()['AcsEvent'].keys()):
                    data = response.json()['AcsEvent']['InfoList'] 
                else:
                    break

                for i in data:
                    if 'employeeNoString' in i.keys():
                        IDs.append(int(i['employeeNoString']))
                        time_data = i['time'] 
                        dt = datetime.fromisoformat(time_data)
                        TIMES.append(dt.strftime("%Y-%m-%d %H:%M:%S"))

                        

            data_final = {'IDs': IDs, 'TIMES': TIMES}
            result_dict = {}

            for key, value in zip(data_final['IDs'], data_final['TIMES']):
                if key in result_dict:
                    result_dict[key].append(value)
                else:
                    result_dict[key] = [value]

                
            emps = []
            for i in result_dict:
                employee_id = http.request.env['hr.employee'].search([('machine_id', '=', i)], limit=1).id

                if employee_id:
                    emps.append(employee_id)
                    date1 = datetime.strptime(min(result_dict[i]), '%Y-%m-%d %H:%M:%S')
                    date2 = datetime.strptime(max(result_dict[i]), '%Y-%m-%d %H:%M:%S')         


                    model = http.request.env['hr.attendance'].sudo()

                    check_in = date1 - timedelta(hours=3)
                    check_out = date2 - timedelta(hours=3)

                    new_attendance_record = model.create({
                        'employee_id': employee_id,
                        'check_in': check_in,
                        'check_out': check_out,
                        'remote': False
                    })


            return json.dumps({
                'success': emps
            })
    
        except Exception as e:
            return json.dumps({
                'Failure': str(e) 
            })