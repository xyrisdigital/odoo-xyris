from odoo import fields, models, api 
from odoo import models, fields, api, exceptions, _
from datetime import timedelta, datetime, time
import datetime


class UserAtt(models.Model):
    _inherit = 'res.users'

    total_wfh = fields.Integer(compute="_compute_sum_wfh")

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            'hours_last_month',
            'hours_last_month_display',
            'attendance_state',
            'last_check_in',
            'last_check_out',
            'total_overtime',
            'attendance_manager_id',
            'display_extra_hours',
            'total_wfh'
        ]

    @api.depends('employee_id')
    def _compute_sum_wfh(self):
        for user in self:
            get_data = self.env['save.res.conf'].sudo().search_read([])


            day_from = get_data[-1]['save_data_to']
            day_to = get_data[-1]['save_date_from']

            count = 0

            for att in user.employee_id.attendance_ids:
                if att.check_in and att.check_in.strftime("%Y-%m-%dT%H:%M:%S+08:00") >= day_from.strftime("%Y-%m-%dT%H:%M:%S+08:00") and att.check_out and att.check_out.strftime("%Y-%m-%dT%H:%M:%S+08:00") <= day_to.strftime("%Y-%m-%dT%H:%M:%S+08:00") and att.remote == True:
                    count += 1

            user.total_wfh = count


    def action_calculate_wfh(self):
        get_data = self.env['save.res.conf'].sudo().search_read([])


        day_from = get_data[-1]['save_data_to']
        day_to = get_data[-1]['save_date_from']

        self.ensure_one()
        # raise ValidationError(f"{day_from}, {day_to}")
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendances This Month"),
            "res_model": "hr.attendance",
            "views": [[self.env.ref('hr_attendance.hr_attendance_employee_simple_tree_view').id, "tree"]],
            "context": {
                "create": 0
            },
            "domain": [('employee_id', '=', self.employee_id.id),
                    ('check_in', ">=", day_from),
                    ('check_in', "<=", day_to),
                    ('remote', '=', True)]
        }




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








      