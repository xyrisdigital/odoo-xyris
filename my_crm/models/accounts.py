from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class Accounts(models.Model):
    _name = 'my_contacts.accounts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Accounts'
    _order = "id desc"

    name = fields.Char(string='Account Name', required=True, tracking=True)
    name_arabic = fields.Char(string="Arabic Name", required=True, tracking=True)
    commercial_name = fields.Char(string="Commercial Name", tracking=True)
    source_of_account = fields.Many2one(comodel_name='utm.source',string='Source Of Account', required=False, tracking=True)


    account_logo = fields.Image("Account Logo", tracking=True)

    parent_id = fields.Many2one('my_contacts.accounts', string='Parent Account (الشركه الأم)', tracking=True)

    industry_type = fields.Selection(string="Industry Type", tracking=True, selection=[
        ('technology', 'Information Technology (IT) and Telecommunications'),
        ('healthcare', 'Healthcare and Pharmaceuticals'),
        ('finance', 'Financial Services'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail and Consumer Goods:'),
        ('energy', 'Energy and Utilities'),
        ('logistics', 'Transportation and Logistics'),
        ('construction', 'Construction and Engineering'),
        ('real estate', 'Real Estate'),
        ('marketing', 'Marketing'),
        ('hospitality', 'Hospitality and Tourism'),
        ('media', 'Media and Entertainment'),
        ('education', 'Education and Training'),
        ('non-profit', 'Nonprofit and Social Services'),
        ('professional', 'Professional Services(Legal/HR/Advertising agency/Marketing Agency)'),
        ('agriculture', 'Agriculture and Agribusiness'),
        ('mining', 'Mining and Extraction'),
        ('others', 'Others')
    ])

    no_employees = fields.Integer(string="Number of Employees", tracking=True)
    cr_no = fields.Integer(string="C.R.#", tracking=True)
    landline = fields.Char(string='Landline (رقم الخط الأرضي)', tracking=True)
    website = fields.Char(string='Website (الموقع الإلكتروني)', tracking=True)
    phone = fields.Char('Phone (التليفون)', required=True, tracking=True)
    email = fields.Char('Email (البريد الإلكتروني)', tracking=True)
    fax = fields.Char(string='FAX', tracking=True)

    address = fields.Char(string='Address (العنوان)', tracking=True)
    building_no = fields.Integer(string = 'Building Number (رقم المبني)', tracking=True)
    floor = fields.Integer(string='Floor Number (رقم الدور)', tracking=True)
    district = fields.Char(string='District (الحي)', tracking=True)
    street = fields.Char('Street (اسم الشارع)', tracking=True)
    city = fields.Char(string="City (المدينه)", tracking=True)
    governorate = fields.Many2one('res.country.state', string="Governorate (المحافظه)", tracking=True)
    postal_code = fields.Integer(string="Postal Code (الرمز البريدي)", tracking=True)
    country = fields.Many2one('res.country', string='Country (البلد)', tracking=True)

    child_count = fields.Integer(string='Number of Child Accounts', compute='_compute_child_count', tracking=True)

    child_ids = fields.One2many('my_contacts.accounts', 'parent_id', tracking=True)


    lead_ids = fields.One2many('crm.lead', 'account_id', tracking=True)

    primary_contact = fields.Many2one('res.partner', string='Primary Contact', compute="_compute_primary_contact", tracking=True)
    contacts = fields.One2many('res.partner', 'account_id', tracking=True)


    account_type = fields.Selection(string="Account Type (نوع الحساب)", selection=[('individual', 'Individual (افراد)'), ('company', 'Company (شركات)')], required=True, tracking=True)
    account_company_type = fields.Selection(string="Company Type", selection=[('corporate', 'Corporate'), ('sme', 'SME')], tracking=True)


    is_company_account = fields.Boolean(compute="_compute_is_company_account", tracking=True)

    _sql_constraints = [
        ('UniqueAccountName', 'unique(name)', 'Sorry, but there is already an account with the same name')
    ]
    
    
    # Phone Validation
    @api.constrains('phone')
    def is_phone(self):
        if self.phone:
            # match = re.match('\\+{0,1}[0-9]{10,12}', self.phone)
            match = re.match('\\+{0,1}[0-9]{11}', self.phone)
            if match == None:
                raise ValidationError('Invalid Phone Number')
            
    # Name Validation English
    @api.constrains('name')
    def is_name_english(self):
        if self.name:
            match = re.match('[\u0627-\u064a]', self.name)
            if match != None:
                raise ValidationError('Invalid English Name')
            
    # Name Validation Arabic
    @api.constrains('name_arabic')
    def is_name_arabic(self):
        if self.name_arabic:
            match = re.match('[\u0627-\u064a]', self.name_arabic)
            if match == None:
                raise ValidationError('Invalid Arabic Name')


    def domain_function(self):
        if self.env.user.has_group('my_crm.crm_lead_chaser') == True:
            return [('share', '=', False)]
        else:            
            return [('share', '=', False), ('id', 'in', [employee.user_id.id for employee in self.env.user.employee_id.child_ids])]

    user_id = fields.Many2one('res.users', string="Account Manager (مسؤول المبيعات)", default=lambda self: self.env.user, 
                              domain=domain_function, tracking=True)



    @api.depends('name')
    def _compute_primary_contact(self):
        for account in self:
            contact = self.env['res.partner'].search([('name', '=', account.name)], limit=1)
            account.primary_contact = contact


    @api.depends('child_ids')
    def _compute_child_count(self):
        for rec in self:
            rec.child_count = len(rec.child_ids)


    def action_view_child_accounts(self):
        action = self.env["ir.actions.actions"]._for_xml_id("my_crm.accounts_action")  
        action['domain'] = [('id', 'in', self.child_ids.ids)] 
        return action      
    


    @api.depends('account_type')
    def _compute_is_company_account(self):
        for account in self:
            if account.account_type == 'company':
                account.is_company_account = True
            else:
                account.is_company_account = False

    @api.model
    def create(self, values):
        record = super(Accounts, self).create(values)
        self.env['res.partner'].create({
            'name': record.name,
            'company_type': 'company' if record.is_company_account else 'person',
            'street': record.street,
            'zip': record.postal_code,
            'city': record.city,
            'state_id': record.governorate.id,
            'country_id': record.country.id,
            'email': record.email,
            'phone': record.phone,
            'website': record.website
        })

        new_vals = {
            'name': values.get('name'),
            'ar_name': values.get('name_arabic'),
            'address': values.get('address'),
            'cr': values.get('cr_no')
        }
        new_record = self.env['crm.view.accounts'].sudo().create(new_vals)

        return record



