from odoo import models, fields, api 
import calendar
from calendar import monthrange
from datetime import datetime
from odoo.exceptions import ValidationError




today = datetime.today()
first_day_of_month = today.replace(day=1)
last_day_of_month = today.replace(day=monthrange(today.year, today.month)[1], hour=23, minute=59, second=59)


class myPayroll(models.Model):
    _inherit = 'hr.employee'


    worked_days = fields.Integer('Worked Days', compute='_compute_worked_days', readonly=True)
    worked_days_plus = fields.Integer('Worked Days Plus', compute='_compute_worked_days_plus', readonly=True)

    month_working_days = fields.Integer('Count Month Days', compute='_compute_month_days')

    emp_effects = fields.One2many('att.effects', 'employee_id')



    @api.depends('resource_calendar_id')
    def _compute_worked_days(self):
        for record in self:

            atts = self.env['hr.attendance'].search([
                ('employee_id', '=', record.id), 
                ('check_in', '<=', last_day_of_month.strftime('%Y-%m-%d %H:%M:%S')), 
                ('check_out', '>=', first_day_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ])


            sum = 0
            for i in atts:
                if i.is_working_day == True:
                    sum += 1
                    
            record.worked_days = sum
            

    @api.depends('resource_calendar_id')
    def _compute_worked_days_plus(self):
        for record in self:

            atts = self.env['hr.attendance'].search([
                ('employee_id', '=', record.id), 
                ('check_in', '<=', last_day_of_month.strftime('%Y-%m-%d %H:%M:%S')), 
                ('check_out', '>=', first_day_of_month.strftime('%Y-%m-%d %H:%M:%S')),
                ('is_working_day', '=', 0)
                ])

                    
            record.worked_days_plus = len(atts)


    # def action_view_attendnace(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("my_payroll.attendance_action")  
    #     action['domain'] = [
    #         ('employee_id', '=', self.id), 
    #         ('check_in', '<=', last_day_of_month.strftime('%Y-%m-%d %H:%M:%S')), 
    #         ('check_out', '>=', first_day_of_month.strftime('%Y-%m-%d %H:%M:%S')),
    #         ('is_working_day', '=', 1)
    #         ]
    #     return action        


    # def action_view_attendnace_plus(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("my_payroll.attendance_action")  
    #     action['domain'] = [
    #         ('employee_id', '=', self.id), 
    #         ('check_in', '<=', last_day_of_month.strftime('%Y-%m-%d %H:%M:%S')), 
    #         ('check_out', '>=', first_day_of_month.strftime('%Y-%m-%d %H:%M:%S')),
    #         ('is_working_day', '=', 0)
    #         ]
    #     return action  

    @api.depends('name')
    def _compute_month_days(self):
        current_month = datetime.now().month
        current_year = datetime.now().year
        total_days_in_month = calendar.monthrange(current_year, current_month)[1]
        days_without_execlusions = 0

        for day in range(1, total_days_in_month + 1):
            if calendar.weekday(current_year, current_month, day) not in [0, 1]:
                days_without_execlusions += 1

        self.month_working_days = days_without_execlusions    


# class MyPayslips(models.Model):
#     _inherit = 'hr.payslip'

#     pl_machine_id = fields.Integer(compute="_compute_machine_id", store=True)



#     @api.depends('employee_id')
#     def _compute_machine_id(self):
#         for pl in self:
#             employee = self.env['hr.employee'].search([('id', '=', pl.employee_id.id)], limit=1)
#             pl.pl_machine_id = employee.machine_id if employee else False    

            
                    
