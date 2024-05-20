from odoo import http, tools
from odoo.http import request

import json
import requests


class CrmChatbot(http.Controller):

    @http.route('/test', auth='public', methods=['POST'], csrf=False)
    def insert_lead(self, **kwargs):

        request_data = json.loads(http.request.httprequest.data)

        name = request_data.get('name')
        phone = request_data.get('phone')
        product = request_data.get('product')
        brand = request_data.get('brand')
        model = request_data.get('model')
        manufacture_year = request_data.get('manufacture-year')
        market_value = request_data.get('market-value')

        model = http.request.env['res.partner'].sudo()

        # new_record = model.create({
        #     'name': name,
        #     'phone': phone,
        # })


        return json.dumps({
            'name': name,
            'phone': phone,
            'product': product,
            'brand': brand,
            'model': model,
            'manufacture_year': manufacture_year,
            'market_value': market_value,
        })