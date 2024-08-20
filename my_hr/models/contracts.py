from odoo import models, api, fields
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, time

def calculate_tax_value(AG3):
    if AG3 <= 40000:
        return 0
    elif AG3 <= 55000:
        return (AG3 - 40000) * 0.1
    elif AG3 <= 70000:
        return (55000 - 40000) * 0.1 + (AG3 - 55000) * 0.15
    elif AG3 <= 200000:
        return (55000 - 40000) * 0.1 + (70000 - 55000) * 0.15 + (AG3 - 70000) * 0.2
    elif AG3 <= 400000:
        return (55000 - 40000) * 0.1 + (70000 - 55000) * 0.15 + (200000 - 70000) * 0.2 + (AG3 - 200000) * 0.225
    elif AG3 <= 600000:
        return (55000 - 40000) * 0.1 + (70000 - 55000) * 0.15 + (200000 - 70000) * 0.2 + (400000 - 200000) * 0.225 + (AG3 - 400000) * 0.25
    elif AG3 <= 700000:
        return 55000 * 0.1 + (70000 - 55000) * 0.15 + (200000 - 70000) * 0.2 + (400000 - 200000) * 0.225 + (AG3 - 400000) * 0.25
    elif AG3 <= 800000:
        return 70000 * 0.15 + (200000 - 70000) * 0.2 + (400000 - 200000) * 0.225 + (AG3 - 400000) * 0.25
    elif AG3 <= 900000:
        return 200000 * 0.2 + (400000 - 200000) * 0.225 + (AG3 - 400000) * 0.25
    elif AG3 <= 1200000:
        return 400000 * 0.225 + (AG3 - 400000) * 0.25
    else:
        return 1200000 * 0.25 + (AG3 - 1200000) * 0.275




class mycontracts(models.Model):
    
    _inherit = 'hr.contract'

    net_salary = fields.Float(string='NET Salary', compute='_calculate_net_salary')
    emp_share = fields.Float(string='Employee Share', help="Please enter the value in percentage", default=11.0)
    medical_ins = fields.Float(string="Medical Ins.")
    soc_ins = fields.Float(string='SOC INS.', compute='_compute_soc_ins')
    tax = fields.Float(string="TAX", compute="_calculate_tax")
    shohdaa = fields.Float(string="Elshohdaa", compute="_calculate_shohdaa")

    day_amount = fields.Float(string="Deduced Days/Day")

    preparation_type = fields.Boolean(string="Probation Period", default=False)
    contract_type = fields.Boolean(string="Contract Period", default=False)



    # @api.onchange('preparation_type')
    @api.model
    def get_date_avarage(self):
        get_data_contract = self.env['hr.contract'].search_read([('state', '=', 'open')])
        get_length = len(get_data_contract)
        get_data = []
        get_data_id = []
        get_data_check = []
        get_data_check_contract = []
        get_date_now = datetime.now().date()
        for rec in range(get_length):
            get_data.append((get_data_contract[rec]['date_start'] + timedelta(days=69)))
            get_data_id.append(get_data_contract[rec]['id'])
            get_data_check.append(get_data_contract[rec]['preparation_type'])
            get_data_check_contract.append(get_data_contract[rec]['contract_type'])
            if get_data[rec] <= get_date_now and get_data_check[rec] == True:
                self.env['mail.activity'].create({
                'res_id': get_data_id[rec],
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.contract')]).id,
                'user_id': 7,
                'summary': 'Preparation Period',
                'note': 'Preparation Period Will Expire',
                'activity_type_id': 4,
                'date_deadline': datetime.now().today(),
                # 'date_deadline': date_deadline,
            })
            
        self.get_date_avarage_2()
                


    @api.model
    def get_date_avarage_2(self):
        # commit
        get_data_contract = self.env['hr.contract'].search_read([('state', '=', 'open')])
        get_length = len(get_data_contract)
        get_data = []
        get_data_id = []
        get_data_check = []
        get_data_check_contract = []
        get_date_now = datetime.now().date()
        for rec in range(get_length):
            # if get_data_contract[rec]['date_end'] != False:
            # get_data.append((get_data_contract[rec]['state']))
            get_data.append((get_data_contract[rec]['date_start'] + timedelta(days=305)))
            # raise UserError('dataaaaaaaaaaa ' + str(get_data))
            get_data_id.append(get_data_contract[rec]['id'])
            # get_data_check.append(get_data_contract[rec]['preparation_type'])
            get_data_check_contract.append(get_data_contract[rec]['contract_type'])
            
            if get_data[rec] <= get_date_now and get_data_check_contract[rec] == True:
                self.env['mail.activity'].create({
                'res_id': get_data_id[rec],
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.contract')]).id,
                'user_id': 7,
                'summary': 'Contract Period',
                'note': 'Contract Period Will Expire',
                'activity_type_id': 4,
                'date_deadline': datetime.now().today(),
                # 'date_deadline': date_deadline,
            })    


    @api.depends('wage')
    def _compute_soc_ins(self):
        for cont in self:
            cont.soc_ins = cont.wage if cont.wage < 12600.0 else 12600.0

    @api.depends('wage')
    def _calculate_shohdaa(self):
        for cont in self:
            cont.shohdaa = cont.wage * 0.0005


    @api.depends('wage')
    def _calculate_tax(self):
        for cont in self:
            tax_pool = ((cont.wage - (cont.soc_ins*cont.emp_share)/100) * 12) - 20000
            cont.tax = calculate_tax_value(tax_pool) / 12


    @api.depends('wage')
    def _calculate_net_salary(self):
        for cont in self:
            cont.net_salary = round(cont.wage - (cont.soc_ins*(cont.emp_share/100) + cont.medical_ins + cont.tax + cont.shohdaa))



