from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import base64
from odoo.tools.misc import clean_context
import re






class Opportunity(models.Model):
    _inherit = 'crm.lead'

    expected_revenue = fields.Monetary('Expected Commission', currency_field='company_currency', tracking=True)

    account_id = fields.Many2one('my_contacts.accounts', string='Account (إسم الشركه)', required=True, tracking=True)


    lead_source = fields.Selection(string="Lead Source", selection=[
        ('whatsapp', 'Whatsapp'),
        ('website', 'Website'),
        ('others', 'Others')
    ], default="others", tracking=True)

    





    fact_findings = fields.Binary(string="Fact Findings")
    meatings_results = fields.Text("Minutes of Meeting", tracking=True)

    customer_data = fields.Binary(string="Customer Data")
   

    stage_number = fields.Integer(compute='_compute_stage_number', ondelete='set null', store=True, precompute=True, tracking=True)


    account_name = fields.Char('Account Name', related='account_id.name', tracking=True)
    parent_account = fields.Char('Parent Account', related='account_id.parent_id.name', tracking=True)
    industry_type = fields.Selection('Industry Type', related="account_id.industry_type", tracking=True)
    no_employees = fields.Char('No. of Employees', related="account_id.no_employees", tracking=True)
    contacts = fields.One2many('res.partner', related="account_id.contacts", tracking=True)
    is_company = fields.Boolean('Is Company?', related="account_id.is_company_account", tracking=True)

  



    @api.onchange('account_id')
    def _onchange_account(self):
        self.partner_name = self.account_id.name
        self.partner_id = self.account_id.primary_contact
        self.email_from = self.account_id.email
        self.phone = self.account_id.phone
        self.street = self.account_id.street
        self.city = self.account_id.city
        self.state_id = self.account_id.governorate
        self.zip = self.account_id.postal_code
        self.country_id = self.account_id.country
        self.contact_name = self.account_id.primary_contact.name
        self.website = self.account_id.website




    @api.depends('account_id')
    def _compute_name(self):
        for lead in self:

            if lead.account_id:
                lead.name = lead.account_id.name + "'s Opportunity"

    @api.depends('stage_id')
    def _compute_stage_number(self):
        for record in self:
            record.stage_number = record.stage_id.id



	
#   ----------Converting to opportunity-----------

    @api.constrains('type')
    def _check_has_activities(self):
        for record in self:
            activity_ids = self.env['crm.activity.report'].search([('lead_id', '=', record.id)])

            flag = False
            
            for i in activity_ids:
                if i.mail_activity_type_id.id in [2, 7, 3]:
                    flag = True    

            if (flag == False and record.type == 'opportunity') :
                raise ValidationError("The lead must have at least one done meeting or call activity")
                
            if flag == True and (not record.fact_findings and not record.meatings_results):
                raise ValidationError("You must insert either the fact findings or MoM")
            



    @api.onchange('partner_id')
    def _change_partner(self):
        for lead in self:
            if lead.stage_number != 1:
                raise ValidationError("Can't change the customer!")
 



    def write(self, values):
        # Add code here  
        res = super(Opportunity, self).write(values)
        for rec in self:
            created_user = rec.create_uid.id
            user_id = self.env.user.id
            if created_user == 4:
                self.env.cr.execute("""UPDATE crm_lead SET  create_uid = """ + str(user_id) + """  WHERE id=""" + str(rec.id) + """  """)
        return res
