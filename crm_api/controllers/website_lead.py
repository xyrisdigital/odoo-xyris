from odoo import http, tools
from odoo.http import request
import json
import requests
import sys 
import os 


class crmWebsite(http.Controller):

    @http.route('/ws-lead', auth='user', methods=['POST'], csrf=False, cors="*")
    def insert_lead(self, **kwargs):

        request_data = json.loads(http.request.httprequest.data)
 
        name = request_data.get('name')
        phone = request_data.get('phone')
        email = request_data.get('email')
        message = request_data.get('message')

        accounts_model = http.request.env['my_contacts.accounts'].sudo()
        lead_model = http.request.env['crm.lead'].sudo()

        account_record = accounts_model.search([('phone', '=', phone)], limit=1) 

        if account_record:
            lead_model.sudo().create({
                'account_id': account_record.id,
                'type': 'lead',
                'name': account_record.name + ' ' + 'Opportunity',
                'phone': phone,
                'lead_source': "website",
                'description': message
            })

        else:
            new_account = accounts_model.sudo().create({
                'name': name,
                'account_type': 'individual',
                'phone': phone,
                'email': email
            })

            lead_model.sudo().create({
                'account_id': new_account.id,
                'type': 'lead',
                'name': new_account.name + ' ' + 'Opportunity',
                'phone': phone,
                'lead_source': "website",
                'description': message
            })




        return json.dumps({
            'Output': "Lead has been created successfully"
        })