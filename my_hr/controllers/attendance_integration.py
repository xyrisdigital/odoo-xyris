from odoo import http, tools
from odoo.http import request

import json
import requests


class att_emp(http.Controller):

    @http.route('/serach_emp', auth='public', methods=['POST'], csrf=False)
    def search_emp(self, **kwargs):

        request_data = json.loads(http.request.httprequest.data)

        id = request_data.get('machine_id')

        model = http.request.env['hr.employeer'].sudo()

        employee_id = model.search([('machine_id', '=', int(id))], limit=1).id

        if employee_id:

            return json.dumps({
                'emp_id': employee_id
            })