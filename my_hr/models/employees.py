from odoo import models, fields, api
from odoo.tools.float_utils import float_round, float_compare
from odoo.tools.translate import _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, time

class MyEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    machine_id = fields.Integer(required=True, copy=False, default=None, tracking=True)



    _sql_constraints = [
        ('UniqueEmpID', 'unique(machine_id)', 'Sorry, but the employee ID must be unique')
    ]


 

class MyCustomEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'


    name_ar = fields.Char(string="الإسم")
    title_ar = fields.Char(related="job_id.name_ar")

    emp_documents = fields.Many2many('ir.attachment', string="Hiring Documents", help='Please attach Documents', copy=False)


class InheritEmployee(models.Model):
    _inherit = 'hr.employee'


    hiring_date = fields.Date(string="Hiring Date")
    
            
    
        



class MyCustomJobs(models.Model):
    _inherit = 'hr.job'

    name_ar = fields.Char(string="اسم الوظيفه", required=True)


# Make New Class
class EmployeeExcusesInherit(models.Model):
    # _name = 'new_module.new_module'
    _inherit = 'hr.leave'

    # def action_approve(self):

    #     if self.holiday_status_id.leave_validation_type == 'both':
    #         user_id = self.env.user.id
    #         get_date_now = datetime.now().date()w
    #         if get_date_now >= (self.create_date.date() + timedelta(days=3)) and \
    #                 user_id != self.employee_ids.parent_id.user_id.id and user_id != self.employee_ids.coach_id.user_id.id:
    #             super(EmployeeExcusesInherit, self).action_approve()
    #         elif user_id == self.employee_ids.parent_id.user_id.id and user_id == self.employee_ids.coach_id.user_id.id:
    #             super(EmployeeExcusesInherit, self).action_approve()
    #         elif get_date_now < (self.create_date.date() + timedelta(days=3)) and \
    #                 user_id != self.employee_ids.parent_id.user_id.id and user_id != self.employee_ids.coach_id.user_id.id:
    #             raise UserError('You Dont Have This Access')
    #             # super(EmployeeExcusesInherit, self).action_approve()
    #     super(EmployeeExcusesInherit, self).action_approve()

    # Send Notification
    # @api.onchange('preparation_type')
    @api.model
    def send_timeoff_notification(self):
        get_date = []
        get_id = []
        get_date_now = datetime.now().date()
        get_data_contract = self.env['hr.leave'].search([('state', '=', 'confirm'),
                        ('holiday_status_id.leave_validation_type', '=', 'both')]).ids
        get_data_length = len(get_data_contract)
        for rec in range(get_data_length):
            get_date_timeoff = self.env['hr.leave'].search([('state', '=', 'confirm'),
                            ('holiday_status_id.leave_validation_type', '=', 'both')])[rec]['create_date'].date()
            get_id_timeoff = self.env['hr.leave'].search([('state', '=', 'confirm'),
                                                               ('holiday_status_id.leave_validation_type', '=',
                                                                'both')])[rec]['id']
            get_date.append(get_date_timeoff)
            get_id.append(get_id_timeoff)
            if (get_date[rec] + timedelta(days=3)) == get_date_now:
                self.env['mail.activity'].create({
                    'res_id': get_id[rec],
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.leave')]).id,
                    'user_id': 6,
                    'summary': 'Attention Timeoff',
                    'note': 'Attention For Employee Timeoff Request',
                    'activity_type_id': 4,
                    'date_deadline': datetime.now().today(),
                    # 'date_deadline': date_deadline,
                })
    
