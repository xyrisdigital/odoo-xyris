from odoo import fields, models, api 
from odoo import models, fields, api, exceptions, _
from odoo.http import request
from datetime import timedelta, datetime, time
import datetime
from odoo.tools import float_round
from odoo.exceptions import ValidationError



class EmpAttendance(models.Model):
    _inherit = 'hr.employee'

    work_entries_ids = fields.One2many('hr.work.entry', 'employee_id')


    def action_open_last_month_attendances(self):

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
            "domain": [('employee_id', '=', self.id),
                    ('check_in', ">=", day_from),
                    ('check_in', "<=", day_to)]
        }

    def action_open_last_month_overtime(self):


        get_data = self.env['save.res.conf'].sudo().search_read([])


        day_from = get_data[-1]['save_data_to']
        day_to = get_data[-1]['save_date_from']


        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Overtime"),
            "res_model": "hr.attendance.overtime",
            "views": [[False, "tree"]],
            "context": {
                "create": 0
            },
            "domain": [('employee_id', '=', self.id),
                    ('date', ">=", day_from),
                    ('date', "<=", day_to)]
        }


    def _compute_hours_last_month(self):
        """
        Compute hours in the current month, if we are the 15th of october, will compute hours from 1 oct to 15 oct
        """

        get_data = self.env['save.res.conf'].sudo().search_read([])


        day_from = get_data[-1]['save_data_to']
        day_to = get_data[-1]['save_date_from']


        for employee in self:
            hours = sum(
                att.worked_hours or 0
                for att in employee.attendance_ids.filtered(
                    lambda att: att.check_in.strftime("%Y-%m-%dT%H:%M:%S+08:00") >= day_from.strftime("%Y-%m-%dT%H:%M:%S+08:00") and att.check_out and att.check_out.strftime("%Y-%m-%dT%H:%M:%S+08:00") <= day_to.strftime("%Y-%m-%dT%H:%M:%S+08:00")
                )
            )

            employee.hours_last_month = round(hours, 2)
            employee.hours_last_month_display = "%g" % employee.hours_last_month





    @api.depends('overtime_ids.duration', 'attendance_ids')
    def _compute_total_overtime(self):
        for employee in self:

            get_data = self.env['save.res.conf'].sudo().search_read([])


            day_from = get_data[-1]['save_data_to']
            day_to = get_data[-1]['save_date_from']


            sum = 0
            if employee.company_id.hr_attendance_overtime:
                for i in employee.overtime_ids:
                    if i.date >= day_from and i.date <= day_to:
                        sum += float_round(i.duration, 2)
                employee.total_overtime = sum


            else:
                employee.total_overtime = 0


      