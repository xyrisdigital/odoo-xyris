from odoo import fields, models, api 
from odoo.exceptions import ValidationError
from datetime import timedelta

class MyTimeOff(models.Model):
    _inherit = 'hr.leave'


    leave_machine_id = fields.Integer(compute="_compute_machine_id", store=True)
    excuse_type = fields.Selection(string="Execuse Type", selection=[('early-leave', 'Early Leave'), ('late-att', 'Late Attendance')])

    is_hour = fields.Boolean()



    @api.onchange('holiday_status_id')
    def _compute_is_hour(self):
        for i in self:
            if i.holiday_status_id.request_unit == 'hour':
                i.is_hour = True
            else:
                i.is_hour = False




    # @api.constrains('date_from', 'date_to')
    # def validate_timeoff_request(self):
    #     for leave in self:
    #         days = []
    #         for day in leave.employee_id.resource_calendar_id.attendance_ids:
    #             days.append(day.dayofweek)

    #         req_date_from = fields.Datetime.from_string(leave.date_from)
    #         req_date_to = fields.Datetime.from_string(leave.date_to)

    #         days_requested = []

            
    #         current_date = req_date_from
    #         while current_date <= req_date_to:
    #             day_of_week = current_date.weekday() 
    #             days_requested.append(day_of_week)
    #             current_date += timedelta(days=1)


    #         flag = False
    #         for i in days_requested:
    #             if i not in days:
    #                 flag = True


    #         if flag:
    #             raise ValidationError("The employee can't request a timeoff during already-off days!")






    @api.depends('employee_id')
    def _compute_machine_id(self):
        for leave in self:
            employee = self.env['hr.employee'].search([('id', '=', leave.employee_id.id)], limit=1)
            leave.leave_machine_id = employee.machine_id if employee else False


    # @api.model
    # def create(self, values):
    #     record = super(MyTimeOff, self).create(values)
    #     self.create_att_effects(record)
    #     return record

    # def create_att_effects(self, timeoff_record):

    #     effect_types = self.determine_effect_type(timeoff_record)

    #     for i in effect_types:
    #         self.env['att.effects'].sudo().create({
    #             'employee_id': timeoff_record.employee_id.id, 
    #             'effect_type': i,
    #             'date_from': timeoff_record.date_from,
    #             'date_to': timeoff_record.date_to,
    #             'hours': effect_types[i]['hours']
    #         }) 


    # def determine_effect_type(self, timeoff_record):
    #     results = {}

    #     if timeoff_record.number_of_days >= 1:
    #         results['timeoff(days)'] = {}
    #         results['timeoff(days)']['hours'] = timeoff_record.number_of_days * 24
    #     else:
    #         results['timeoff(hours)'] = {}
    #         results['timeoff(hours)']['hours'] = timeoff_record.number_of_days * 8            

    #     return results               