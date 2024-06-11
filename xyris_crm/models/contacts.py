from odoo import fields, models, api


class MyContacts(models.Model):
    _inherit = "res.partner"

    account_id = fields.Many2one('my_contacts.accounts', string="Account")