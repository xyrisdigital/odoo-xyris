from odoo import fields, models, api 
from odoo import models, fields, api, exceptions, _
from datetime import timedelta, datetime, time
import datetime


class UserAtt(models.Model):
    _inherit = 'res.users'




    def action_open_last_month_attendances(self):

        today = datetime.date.today()

        if today.day >= 21:
            start_date = today.replace(day=21)  
            end_date = today
        else:
            end_date = today.replace(day=20) 
            start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=21) 

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendances This Month"),
            "res_model": "hr.attendance",
            "views": [[self.env.ref('hr_attendance.hr_attendance_employee_simple_tree_view').id, "tree"]],
            "context": {
                "create": 0
            },
            "domain": [('employee_id', '=', self.employee_id.id),
                    ('check_in', ">=", start_date.strftime('%Y-%m-%d 00:00:00')),
                    ('check_in', "<=", end_date.strftime('%Y-%m-%d 23:59:59'))]
        }


    def action_open_last_month_overtime(self):

        today = datetime.date.today()

        if today.day >= 21:
            start_date = today.replace(day=21)  
            end_date = today
        else:
            end_date = today.replace(day=20) 
            start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=21) 

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Overtime"),
            "res_model": "hr.attendance.overtime",
            "views": [[False, "tree"]],
            "context": {
                "create": 0
            },
            "domain": [('employee_id', '=', self.employee_id.id),
                    ('date', ">=", start_date.strftime('%Y-%m-%d 00:00:00')),
                    ('date', "<=", end_date.strftime('%Y-%m-%d 23:59:59'))]
        }








      