from odoo import http, tools
from odoo.http import request
import json
import requests
import sys 
import os 
import base64

app_id = '458418763578482'
app_secret = '68eb587023e3b9f0885072cb2e755859'
short_lived_token = 'EAAGg7eZBPvHIBO2FBN3j3GTwf973oGlgmeD4Hs0kGkFiCDoRVT9WfByptZCxfjDsScyVhQWkkIzc8QzhPvZAEPSddnElFOPF3THRDnV2p2reRZArE4QNMUWqP0JsMjSo9ZCCHWd538W71xWY72v3qA04jDLZBip7PA1XRR3QJUlK0XSWgRLwafwjVY9netuGbynFv0bXcd9TmVywdwUHb3VF7sgU8DJzV6UdrVanMmMbBWr0ivZAiQZD'


def refresh_access_token(app_id, app_secret, short_lived_token):
    url = f"https://graph.facebook.com/v20.0/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_lived_token
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error refreshing token: {response.json()}")




class SendMessage(http.Controller):

    @http.route('/api/send_message/<model("res.partner"):partner>', type='http', auth='user', methods=['POST'], csrf=False)
    def send_message(self, partner):

        body = f"""
Dear {partner.complete_name},<br/><br/>

Thank you for attending IBM Cloud Platform Event! We’re excited to have you with us, and look forward to an engaging experience.<br/><br/>

As a valued attendee, we want to share more about our company. Please find our company profile attached for your reference.<br/><br/>

If you have any questions or need further information, please feel free to reach out. We’re here to help!<br/><br/>
Also you will find the updated agenda attached!<br/><br/>
Thank you once again for joining us. Enjoy the event!

"""

      
        try:
            mail_message = http.request.env['mail.mail'].create({
            'email_from': 'info@xyrisdigital.com',    
            'email_to': partner.email,
            'subject': "Xyris Company Profile",
            'body_html': body,
            'attachment_ids': [1156, 1158]
            })

            # Send the email
            mail_message.send()
        except Exception as e:
            return request.make_response(json.dumps({'error': f"Failed to send email: {str(e)}"}), headers={'Content-Type': 'application/json'})

        # Sending WhatsApp message
        try:
            # WhatsApp Business API credentials
            whatsapp_api_url = 'https://graph.facebook.com/v20.0/379402761917175/messages'
            # access_token = refresh_access_token(app_id, app_secret, short_lived_token)
            access_token = "EAAGg7eZBPvHIBO84Edyw26Hvvic9zfYPxzP6kuGYa5djZCGiMrQEZChWTQEZBrih8r26qGZCPRWL3k6CtYiTQcEEZBdiPIOVtUlh903KTq4mpGdHr8FaTizoKPwa8nY9TyTugQWEXOy6Moz2ICxKED77B6bfmaIzQNIrsDXfA4ontYVZC9f9KH0RPJPyAX6cvgLsccsxM5Hut3cfNKS"


            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            data = {
                "messaging_product": "whatsapp",
                "to": partner.mobile,
                "type": "template",
                "template": {
                    "name": "xyris_ibm_invitation", 
                    "language": {
                        "code": "en"
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": f"{partner.complete_name}"  
                                }
                            ]
                        }
                    ]
                }
            }


            response = requests.post(whatsapp_api_url, data=json.dumps(data), headers=headers)
            if response.status_code != 200:
                return request.make_response(json.dumps({'error': f"Failed to send WhatsApp message: {response.text}"}), headers={'Content-Type': 'application/json'})

        except Exception as e:
            return request.make_response(json.dumps({'error': f"Failed to send WhatsApp message: {str(e)}"}), headers={'Content-Type': 'application/json'})

        return request.make_response(json.dumps({'success': 'Email and WhatsApp message sent successfully'}), headers={'Content-Type': 'application/json'})