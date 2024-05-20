from odoo import fields, models, api 


class myDocuments(models.Model):
    _name = 'my_hr.documents'

    name = fields.Char(string='Document Name', required=True)
    document_template = fields.Binary(string="Document Template", required=True)


    
 

