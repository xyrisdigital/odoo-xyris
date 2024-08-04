from odoo import fields, models, api 
from pytz import timezone
from odoo.addons.resource.models.utils import Intervals
from collections import defaultdict
from operator import itemgetter
from datetime import timedelta, datetime, time
from odoo.osv.expression import AND, OR
from odoo.tools.float_utils import float_is_zero
import pytz
import math


def haversine(self, lon1, lat1, lon2, lat2):
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    r = 6371
    return c * r


class myAttendance(models.Model):
    _inherit = 'hr.attendance'

    status = fields.Boolean(string="Status", compute="_compute_status")
    percentage = fields.Float(string='Percentage', compute='_compute_percentage')
    att_machine_id = fields.Integer(compute="_compute_machine_id", store=True)
    is_working_day = fields.Boolean(string="Is_work", compute="_compute_is_work_day", store=True)
    has_leave = fields.Boolean(string="Has Leave", compute="_compute_has_leave")
    remote = fields.Boolean(string="Remote", default=True)



    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in and attendance.employee_id:
                calendar = attendance._get_employee_calendar()
                resource = attendance.employee_id.resource_id
                tz = timezone(calendar.tz)
                check_in_tz = attendance.check_in.astimezone(tz)
                check_out_tz = attendance.check_out.astimezone(tz)
                lunch_intervals = calendar._attendance_intervals_batch(
                    check_in_tz, check_out_tz, resource, lunch=True)
                attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) - lunch_intervals[resource.id]
                delta = sum((i[1] - i[0]).total_seconds() for i in attendance_intervals)
                total_hours = delta / 3600.0
                
                if attendance.remote == True:

                    if total_hours <= calendar.hours_per_day:
                        attendance.worked_hours = total_hours
                    else:
                        attendance.worked_hours = calendar.hours_per_day

                else:
                    attendance.worked_hours = total_hours
            else:
                attendance.worked_hours = False




    @api.depends('worked_hours')
    def _compute_overtime_hours(self):
        att_progress_values = dict()
        if self.employee_id:
            self.env['hr.attendance'].flush_model(['worked_hours'])
            self.env['hr.attendance.overtime'].flush_model(['duration'])
            self.env.cr.execute('''
                SELECT att.id as att_id,
                       att.worked_hours as att_wh,
                       ot.id as ot_id,
                       ot.duration as ot_d,
                       ot.date as od,
                       att.check_in as ad
                  FROM hr_attendance att
             INNER JOIN hr_attendance_overtime ot
                    ON date_trunc('day',att.check_in) = date_trunc('day', ot.date)
                    AND date_trunc('day',att.check_out) = date_trunc('day', ot.date)
                    AND att.employee_id IN %s
                    AND att.employee_id = ot.employee_id
                    ORDER BY att.check_in DESC
            ''', (tuple(self.employee_id.ids),))
            a = self.env.cr.dictfetchall()
            grouped_dict = dict()
            for row in a:
                if row['ot_id'] and row['att_wh']:
                    if row['ot_id'] not in grouped_dict:
                        grouped_dict[row['ot_id']] = {'attendances': [(row['att_id'], row['att_wh'])], 'overtime_duration': row['ot_d']}
                    else:
                        grouped_dict[row['ot_id']]['attendances'].append((row['att_id'], row['att_wh']))

            for ot in grouped_dict:
                ot_bucket = grouped_dict[ot]['overtime_duration']
                for att in grouped_dict[ot]['attendances']:
                    if ot_bucket > 0:
                        sub_time = att[1] - ot_bucket
                        if sub_time < 0:
                            att_progress_values[att[0]] = 0
                            ot_bucket -= att[1]
                        else:
                            att_progress_values[att[0]] = float(((att[1] - ot_bucket) / att[1])*100)
                            ot_bucket = 0
                    else:
                        att_progress_values[att[0]] = 100
        for attendance in self:
            if attendance.remote != True:
                attendance.overtime_hours = attendance.worked_hours * ((100 - att_progress_values.get(attendance.id, 100))/100)
            else:
                attendance.overtime_hours = attendance.worked_hours * ((100 - att_progress_values.get(attendance.id, 100))/100)
                if attendance.overtime_hours > 0:
                    attendance.overtime_hours = 0.0

    def _update_overtime(self, employee_attendance_dates=None):
        if employee_attendance_dates is None:
            employee_attendance_dates = self._get_attendances_dates()

        overtime_to_unlink = self.env['hr.attendance.overtime']
        overtime_vals_list = []
        affected_employees = self.env['hr.employee']
        for emp, attendance_dates in employee_attendance_dates.items():
            # get_attendances_dates returns the date translated from the local timezone without tzinfo,
            # and contains all the date which we need to check for overtime
            attendance_domain = []
            for attendance_date in attendance_dates:
                attendance_domain = OR([attendance_domain, [
                    ('check_in', '>=', attendance_date[0]), ('check_in', '<', attendance_date[0] + timedelta(hours=24)),
                ]])
            attendance_domain = AND([[('employee_id', '=', emp.id)], attendance_domain])

            # Attendances per LOCAL day
            attendances_per_day = defaultdict(lambda: self.env['hr.attendance'])
            all_attendances = self.env['hr.attendance'].search(attendance_domain)
            for attendance in all_attendances:
                check_in_day_start = attendance._get_day_start_and_day(attendance.employee_id, attendance.check_in)
                attendances_per_day[check_in_day_start[1]] += attendance

            # As _attendance_intervals_batch and _leave_intervals_batch both take localized dates we need to localize those date
            start = pytz.utc.localize(min(attendance_dates, key=itemgetter(0))[0])
            stop = pytz.utc.localize(max(attendance_dates, key=itemgetter(0))[0] + timedelta(hours=24))

            # Retrieve expected attendance intervals
            calendar = emp.resource_calendar_id or emp.company_id.resource_calendar_id
            expected_attendances = calendar._attendance_intervals_batch(
                start, stop, emp.resource_id
            )[emp.resource_id.id]
            # Substract Global Leaves and Employee's Leaves
            leave_intervals = calendar._leave_intervals_batch(
                start, stop, emp.resource_id, domain=AND([
                    self._get_overtime_leave_domain(),
                    [('company_id', 'in', [False, emp.company_id.id])],
                ])
            )
            expected_attendances -= leave_intervals[False] | leave_intervals[emp.resource_id.id]

            # working_times = {date: [(start, stop)]}
            working_times = defaultdict(lambda: [])
            for expected_attendance in expected_attendances:
                # Exclude resource.calendar.attendance
                working_times[expected_attendance[0].date()].append(expected_attendance[:2])

            overtimes = self.env['hr.attendance.overtime'].sudo().search([
                ('employee_id', '=', emp.id),
                ('date', 'in', [day_data[1] for day_data in attendance_dates]),
                ('adjustment', '=', False),
            ])

            company_threshold = emp.company_id.overtime_company_threshold / 60.0
            employee_threshold = emp.company_id.overtime_employee_threshold / 60.0

            for day_data in attendance_dates:
                attendance_date = day_data[1]
                attendances = attendances_per_day.get(attendance_date, self.browse())
                unfinished_shifts = attendances.filtered(lambda a: not a.check_out)
                overtime_duration = 0
                overtime_duration_real = 0
                # Overtime is not counted if any shift is not closed or if there are no attendances for that day,
                # this could happen when deleting attendances.
                if not unfinished_shifts and attendances:
                    # The employee usually doesn't work on that day
                    if not working_times[attendance_date]:
                        # User does not have any resource_calendar_attendance for that day (week-end for example)
                        overtime_duration = sum(attendances.mapped('worked_hours'))
                        overtime_duration_real = overtime_duration
                    # The employee usually work on that day
                    else:
                        # Compute start and end time for that day
                        planned_start_dt, planned_end_dt = False, False
                        planned_work_duration = 0
                        for calendar_attendance in working_times[attendance_date]:
                            planned_start_dt = min(planned_start_dt, calendar_attendance[0]) if planned_start_dt else calendar_attendance[0]
                            planned_end_dt = max(planned_end_dt, calendar_attendance[1]) if planned_end_dt else calendar_attendance[1]
                            planned_work_duration += (calendar_attendance[1] - calendar_attendance[0]).total_seconds() / 3600.0
                        # Count time before, during and after 'working hours'
                        pre_work_time, work_duration, post_work_time = 0, 0, 0

                        for attendance in attendances:
                            # consider check_in as planned_start_dt if within threshold
                            # if delta_in < 0: Checked in after supposed start of the day
                            # if delta_in > 0: Checked in before supposed start of the day
                            local_check_in = pytz.utc.localize(attendance.check_in)
                            delta_in = (planned_start_dt - local_check_in).total_seconds() / 3600.0

                            # Started before or after planned date within the threshold interval
                            if (delta_in > 0 and delta_in <= company_threshold) or\
                                (delta_in < 0 and abs(delta_in) <= employee_threshold):
                                local_check_in = planned_start_dt
                            local_check_out = pytz.utc.localize(attendance.check_out)

                            # same for check_out as planned_end_dt
                            delta_out = (local_check_out - planned_end_dt).total_seconds() / 3600.0
                            # if delta_out < 0: Checked out before supposed start of the day
                            # if delta_out > 0: Checked out after supposed start of the day

                            # Finised before or after planned date within the threshold interval
                            if (delta_out > 0 and delta_out <= company_threshold) or\
                                (delta_out < 0 and abs(delta_out) <= employee_threshold):
                                local_check_out = planned_end_dt

                            # There is an overtime at the start of the day
                            if local_check_in < planned_start_dt:
                                pre_work_time += (min(planned_start_dt, local_check_out) - local_check_in).total_seconds() / 3600.0
                            # Interval inside the working hours -> Considered as working time
                            if local_check_in <= planned_end_dt and local_check_out >= planned_start_dt:
                                start_dt = max(planned_start_dt, local_check_in)
                                stop_dt = min(planned_end_dt, local_check_out)
                                work_duration += (stop_dt - start_dt).total_seconds() / 3600.0
                                # remove lunch time from work duration
                                lunch_intervals = calendar._attendance_intervals_batch(start_dt, stop_dt, emp.resource_id, lunch=True)
                                work_duration -= sum((i[1] - i[0]).total_seconds() / 3600.0 for i in lunch_intervals[emp.resource_id.id])

                            # There is an overtime at the end of the day
                            if local_check_out > planned_end_dt:
                                post_work_time += (local_check_out - max(planned_end_dt, local_check_in)).total_seconds() / 3600.0

                        # Overtime within the planned work hours + overtime before/after work hours is > company threshold
                        overtime_duration = work_duration - planned_work_duration
                        if pre_work_time > company_threshold:
                            overtime_duration += pre_work_time
                        if post_work_time > company_threshold:
                            overtime_duration += post_work_time
                        # Global overtime including the thresholds
                        overtime_duration_real = sum(attendances.mapped('worked_hours')) - planned_work_duration

                overtime = overtimes.filtered(lambda o: o.date == attendance_date)
                if not float_is_zero(overtime_duration, 2) or unfinished_shifts:
                    # Do not create if any attendance doesn't have a check_out, update if exists
                    if unfinished_shifts:
                        overtime_duration = 0

                    if self.remote == True:
                        if overtime_duration > 0: 
                            overtime_duration = 0.0

                    if not overtime and overtime_duration:
                        overtime_vals_list.append({
                            'employee_id': emp.id,
                            'date': attendance_date,
                            'duration': overtime_duration,
                            'duration_real': overtime_duration_real,
                        })
                    elif overtime:
                        overtime.sudo().write({
                            'duration': overtime_duration,
                            'duration_real': overtime_duration
                        })
                        affected_employees |= overtime.employee_id
                elif overtime:
                    overtime_to_unlink |= overtime
        created_overtimes = self.env['hr.attendance.overtime'].sudo().create(overtime_vals_list)
        employees_worked_hours_to_compute = (affected_employees.ids +
                                             created_overtimes.employee_id.ids +
                                             overtime_to_unlink.employee_id.ids)
        overtime_to_unlink.sudo().unlink()
        self.env.add_to_compute(self._fields['overtime_hours'],
                                self.search([('employee_id', 'in', employees_worked_hours_to_compute)]))



    @api.depends('check_in', 'employee_id')
    def _compute_is_work_day(self):
        for rec in self:
            days = rec.employee_id.resource_calendar_id.attendance_ids.mapped('dayofweek')

            date_attended = fields.Datetime.from_string(rec.check_in)
            day_number = date_attended.weekday()

            if str(day_number) in days:
                rec.is_working_day = True
            else:
                rec.is_working_day = False


    @api.depends('employee_id')
    def _compute_machine_id(self):
        for att in self:
            employee = self.env['hr.employee'].search([('id', '=', att.employee_id.id)], limit=1)
            att.att_machine_id = employee.machine_id if employee else False
        

    @api.depends('worked_hours')
    def _compute_status(self):
        for att in self:
            if att.worked_hours >= 8:
                att.status = True
            else:
                att.status = False    


    @api.depends('worked_hours')
    def _compute_percentage(self):
        for record in self:
            avg_hours = record.employee_id.resource_calendar_id.hours_per_day
            record.percentage = (record.worked_hours / avg_hours) * 100


    @api.depends('employee_id')
    def _compute_has_leave(self):
        for att in self:
            leave = self.env['hr.leave'].search([
                ('employee_id', '=', att.employee_id.id), 
                ('number_of_days', '<', 1),
                ('date_from', '>=', att.check_in.date()),
                ('date_from', '<', (att.check_in + timedelta(days=1)).date())
                ])
            
            if leave:
                for req in leave:
                    date1 = fields.Date.to_date(req.date_from)
                    date2 = fields.Date.to_date(att.check_in)

                    if date1 == date2:
                        att.has_leave = True
                    else:
                        att.has_leave = False
            else:
                att.has_leave = False      

    @api.model
    def create(self, values):
        record = super(myAttendance, self).create(values)

        fixed_lon = 29.9892736
        fixed_lat = 31.2737792

        record_lon = values.get('in_latitude')
        record_lat = values.get('in_longitude')

        if record_lon and record_lat:

            distance = self.haversine(record_lon, record_lat, fixed_lon, fixed_lat)

            distance_in_meters = distance * 1000

            if distance_in_meters > 200:
                record.remote = True
            else:
                record.remote = False

        # self.create_att_effects(record)
        return record



    # def create_att_effects(self, attendance_record):
    #     effect_types = self.determine_effect_type(attendance_record)

    #     att_hours = attendance_record.check_out - attendance_record.check_in

    #     self.env['att.effects'].create({
    #         'employee_id': attendance_record.employee_id.id, 
    #         'effect_type': 'att',
    #         'hours': att_hours.total_seconds() / 3600.0,
    #         'date_from': attendance_record.check_in,
    #         'date_to': attendance_record.check_out
    #     })         

    #     for i in effect_types:
    #         description = ''
    #         if i == 'lateatt':
    #            get_data = self.env['res.config.settings'].search_read([])
    #            get_data_len = len(get_data)

    #            for rec in range(get_data_len):
    #                get_date_from = get_data[rec]['my_custom_field1_id']
    #                get_date_to = get_data[rec]['my_custom_field2_id']


    #            lateatt_count = self.env['att.effects'].search_count([('effect_type', '=', 'lateatt'),
    #                                     ('employee_id', '=', attendance_record.employee_id.id),
    #                                     ('date_from', '>=', get_date_from), ('date_to', '<=', get_date_to)])
            
    #            if lateatt_count == 0:
    #                description = 'انذار'
    #            elif lateatt_count == 1:
    #                description = 'خصم ربع يوم'
    #            elif lateatt_count == 2:
    #                description = 'خصم نصف يوم'
    #            elif lateatt_count == 3:
    #                description = 'خصم يوم'

    #         self.env['att.effects'].create({
    #             'employee_id': attendance_record.employee_id.id,
    #             'effect_type': i,
    #             'hours': effect_types[i]['hours'],
    #             'minutes': effect_types[i]['minutes'],
    #             'date_from': attendance_record.check_in,
    #             'date_to': attendance_record.check_out,
    #             'description': description
    #         })


    # def determine_effect_type(self, attendance_record):
    #     results = {}
    #     resource_calendar = attendance_record.employee_id.resource_calendar_id

    #     attendace_check_in = fields.Datetime.from_string(attendance_record.check_in)
    #     attendace_check_out = fields.Datetime.from_string(attendance_record.check_out)

    #     day_of_week = attendace_check_in.weekday()

    #     attendance_rule = resource_calendar.attendance_ids.filtered(lambda rule: rule.dayofweek == str(day_of_week))

    #     if attendance_rule:
    #         # check_in_hour = attendace_check_in.hour + 2.0
    #         check_in_hour = attendace_check_in.hour
    #         check_in_minutes = attendace_check_in.minute
    #         # Get Set Time Hours And Minutes
    #         get_data = self.env['hr.employee'].search([('id', '=', attendance_record.employee_id.id)])
    #         for rec in get_data:
    #             get_set_time_hours = rec.set_time_hours
    #             get_set_time_minutes = rec.set_time_minutes
    #         target_time = time(get_set_time_hours, get_set_time_minutes)

    #         hour_value_in = attendace_check_in.hour + (attendace_check_in.minute / 60.0)
    #         hour_value_out = attendace_check_out.hour + (attendace_check_out.minute / 60.0)


    #         if (check_in_hour, check_in_minutes) < (target_time.hour, target_time.minute):
    #             if (attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0 < 8.0:
    #                 pass
    #                 # results['shortage'] = {}
    #                 # results['shortage']['hours'] = (8 - ((attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0))*60 //60
    #                 # results['shortage']['minutes'] = (8 - ((attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0))*60 % 60
    #             else:
    #                 results['overtime'] = {}
    #                 results['overtime']['hours'] = (((attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0) - 8.0) *60 //60
    #                 results['overtime']['minutes'] = (((attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0) - 8.0) *60 %60

        
    #         else:
    #             results['lateatt'] = {}
    #             results['lateatt']['hours'] = (((hour_value_in + 2.0) - 10.5) * 60) // 60
    #             # results['lateatt']['hours'] = (((hour_value_in + 0) - 9.5) * 60) // 60
    #             results['lateatt']['minutes'] = (((hour_value_in + 2.0) - 10.5) * 60) % 60
    #             # results['lateatt']['minutes'] = (((hour_value_in + 0) - 9.5) * 60) % 60


    #             if (attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0 < 8.0:
    #                 pass
    #                 # results['shortage'] = {}
    #                 # results['shortage']['hours'] = (8 - ((attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0))*60 //60
    #                 # results['shortage']['minutes'] = (8 - ((attendance_record.check_out - attendance_record.check_in).total_seconds() / 3600.0))*60 % 60


            
            

    #     else:
    #         results['extradays'] = {}
    #         hour_value_in = attendace_check_in.hour + (attendace_check_in.minute / 60.0)
    #         hour_value_out = attendace_check_out.hour + (attendace_check_out.minute / 60.0)
    #         worked_hours = hour_value_out - hour_value_in
    #         results['extradays']['hours'] = (worked_hours * 60) // 60
    #         results['extradays']['minutes'] = (worked_hours * 60) % 60

    #     return results



class SaveResConfigSettings(models.Model):
    _name = 'save.res.conf'


    save_data_to = fields.Date(string='Date From')
    save_date_from = fields.Date(string='Date To')






class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    my_custom_field1_id = fields.Date(string='Date From', store=True)
    my_custom_field2_id = fields.Date(string='Date To', store=True)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()


        param.set_param('my_payroll.my_custom_field1_id', self.my_custom_field1_id)
        param.set_param('my_payroll.my_custom_field2_id', self.my_custom_field2_id)

        return res


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        res.update(
            my_custom_field1_id = params.get_param('my_payroll.my_custom_field1_id'),
            my_custom_field2_id = params.get_param('my_payroll.my_custom_field2_id'),
        )

        return res

    @api.model
    def create(self, values):
        res = super(ResConfigSettings, self).create(values)

        for rec in res:
            date_to = rec.my_custom_field1_id
            date_from = rec.my_custom_field2_id

        get_count = self.env['save.res.conf'].search_count([])



        if get_count == 0:
            self.env['save.res.conf'].create({
                'save_data_to': date_to,
                'save_date_from': date_from
            })
            
        elif get_count > 0:
            get_id = self.env['save.res.conf'].search([])[-1].id

            now1 = datetime.strftime(date_to, "%Y-%m-%d")
            now2 = datetime.strftime(date_from, "%Y-%m-%d")

            self.env.cr.execute("""UPDATE save_res_conf SET save_data_to= CAST('""" +str(now1)+ """' AS DATE) ,save_date_from= CAST('""" +str(now2)+ """' AS DATE)   WHERE id=""" + str(get_id) + """  """)


        data_get = self.env['save.res.conf'].search_read([])


        return res


