from odoo import models, api, fields
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class Att_Report(models.Model):
    _name = 'att.report'
    _rec_name = 'employee_name'
    
    employee_id = fields.Integer(string='Employee ID')

    employee_name = fields.Many2one('hr.employee',
        string='Employee Name'
    )
    
    required_hours = fields.Char(
        string='Required Hours'
    )
    
    remote_hours = fields.Char(
        string='Remote Hours'
    )

    office_hours = fields.Char(
        string='Office Hours'
    )
    
    excuses = fields.Char(
        string='Excuses'
    )

    overtime = fields.Char(
        string='Overtime'
    )    

    total_hours = fields.Char(
        string='Total Hours'
    )     

    percentage = fields.Integer(
        string='Percentage'
    )






    def calculate_report(self, public_days = None, start_date = None, end_date = None):
        query = """
            SELECT 
    employee_id,
    -- Required hours calculation
    ((((SELECT 
        count(*) - """ + str(public_days) + """
    	FROM 
        generate_series(CAST('""" + str(start_date) + """' AS DATE)::date, CAST('""" + str(end_date) + """' AS DATE)::date, '1 day'::interval) AS date
    	WHERE 
        DATE_PART('dow', date) NOT IN (5, 6))) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)) -
    	(
    	COALESCE(
    	    ((WITH leave_dates AS 
			(
    SELECT 
        employee_id,
        number_of_days,
        generate_series(request_date_from::timestamp, request_date_to::timestamp, '1 day')::date AS leave_date
    FROM 
        hr_leave  
		) 
		SELECT 
		sum(case when number_of_days >= 1 then 1 else number_of_days end) as real_days 
		FROM leave_dates 
		WHERE leave_date 
		BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE) AND leave_dates.employee_id = a.employee_id
		GROUP BY employee_id) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)
			),interval '0 hours'))-
			(SELECT 
    ((COALESCE((CASE 
                WHEN Date_start - CAST('""" + str(start_date) + """' AS DATE) > 0 AND Date_start - CAST('""" + str(start_date) + """' AS DATE) < 30 
                THEN Date_start - CAST('""" + str(start_date) + """' AS DATE) 
                ELSE 0 
              END), 0) 
     + 
     COALESCE((CASE 
                WHEN CAST('""" + str(end_date) + """' AS DATE) - date_end > 0 AND CAST('""" + str(end_date) + """' AS DATE) - date_end < 30 
                THEN CAST('""" + str(end_date) + """' AS DATE) - date_end 
                ELSE 0 
              END), 0)) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)) AS total_hours
		FROM hr_contract where hr_contract.employee_id = a.employee_id )) AS req_hours,
     
    COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) 
     FROM hr_attendance b 
     WHERE a.employee_id = b.employee_id 
       AND remote = TRUE 
       AND check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)),0) * interval '1 hour' AS Remote_Hours,
       
    (SELECT SUM(COALESCE(worked_hours, 0)) 
     FROM hr_attendance b 
     WHERE a.employee_id = b.employee_id 
       AND remote = FALSE 
       AND check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)) * interval '1 hour' AS Office_Hours,
       
    SUM(COALESCE((SELECT number_of_days * interval '1 hours' 
                  FROM hr_leave 
                  WHERE holiday_status_id = 11 
                    AND hr_leave.employee_id = a.employee_id 
                    AND hr_leave.request_date_from  BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)
				    AND hr_leave.state = 'validate'
                    LIMIT 1), interval '0 hours') )  AS Ex,
                  
    (SELECT SUM(COALESCE(overtime_hours, 0)) 
     FROM hr_attendance b 
     WHERE check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE) 
     AND a.employee_id = b.employee_id) * interval '1 hour' AS OVR,
       
    -- Total Hours calculation
    (
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = TRUE 
                    AND check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)), interval '0 hours') + 
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = FALSE 
                    AND check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)), interval '0 hours') + 
        COALESCE(SUM(COALESCE((SELECT number_of_days * interval '1 hours'
                               FROM hr_leave 
                               WHERE holiday_status_id = 11 
                                 AND hr_leave.employee_id = a.employee_id 
                                 AND hr_leave.request_date_from BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)
                                 AND hr_leave.state = 'validate'
                               LIMIT 1), interval '0 hours')), interval '0 hours')
    ) AS total_hours,


    -- Percentage calculation using inline req_hours calculation with FLOOR applied
    FLOOR((EXTRACT(EPOCH FROM (
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = TRUE 
                    AND check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)), interval '0 hours') + 
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = FALSE 
                    AND check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE)), interval '0 hours') + 
        COALESCE(SUM(COALESCE((SELECT number_of_days * interval '1 hours'
                               FROM hr_leave 
                               WHERE holiday_status_id = 11 
                                 AND hr_leave.employee_id = a.employee_id 
                                 AND hr_leave.request_date_from BETWEEN '2024-10-01' AND '2024-10-30'
                                 AND hr_leave.state = 'validate'
                               LIMIT 1), interval '0 hours')), interval '0 hours')
    )) / EXTRACT(EPOCH FROM ((((SELECT 
        count(*) - """ + str(public_days) + """ 
    	FROM 
        generate_series(CAST('""" + str(start_date) + """' AS DATE)::date, CAST('""" + str(end_date) + """' AS DATE)::date, '1 day'::interval) AS date
    	WHERE 
        DATE_PART('dow', date) NOT IN (5, 6))) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)) -
    	(
    	COALESCE(
    	    ((WITH leave_dates AS 
			(
    SELECT 
        employee_id,
        number_of_days,
        generate_series(request_date_from::timestamp, request_date_to::timestamp, '1 day')::date AS leave_date
    FROM 
        hr_leave  
		) 
		SELECT 
		sum(case when number_of_days >= 1 then 1 else number_of_days end) as real_days 
		FROM leave_dates 
		WHERE leave_date 
		BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE) AND leave_dates.employee_id = a.employee_id
		GROUP BY employee_id) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)
			),interval '0 hours'))-
			(SELECT 
    ((COALESCE((CASE 
                WHEN Date_start - CAST('""" + str(start_date) + """' AS DATE) > 0 AND Date_start - CAST('""" + str(start_date) + """' AS DATE) < 30 
                THEN Date_start - CAST('""" + str(start_date) + """' AS DATE) 
                ELSE 0 
              END), 0) 
     + 
     COALESCE((CASE 
                WHEN CAST('""" + str(end_date) + """' AS DATE) - date_end > 0 AND CAST('""" + str(end_date) + """' AS DATE) - date_end < 30 
                THEN CAST('""" + str(end_date) + """' AS DATE) - date_end 
                ELSE 0 
              END), 0)) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)) AS total_hours
		FROM hr_contract where hr_contract.employee_id = a.employee_id )))) * 100) AS percentage

FROM hr_attendance a 
WHERE check_in BETWEEN CAST('""" + str(start_date) + """' AS DATE) AND CAST('""" + str(end_date) + """' AS DATE) and Employee_id in (select Employee_id From hr_contract where state = 'open' )
GROUP BY employee_id;
        """
        # self.env.cr.execute(query, (self.start_date, self.end_date))
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()

        # raise UserError('dataaaaaaaaaaaaaaa ' + str(result))

        


        get_length = len(result)

        for rec in range(get_length):

            # Calculate total hours - Required Hours
            total_hours = result[rec][1].days * 24 + result[rec][1].seconds // 3600
            remaining_seconds = result[rec][1].seconds % 3600
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60


            # Calculate total hours - Remote Hours
            total_hours_remote = result[rec][2].days * 24 + result[rec][2].seconds // 3600
            remaining_seconds_remote = result[rec][2].seconds % 3600
            minutes_remote = remaining_seconds_remote // 60
            seconds_remote = remaining_seconds_remote % 60


            # Calculate total hours - Office Hours
            total_hours_office = result[rec][3].days * 24 + result[rec][3].seconds // 3600
            remaining_seconds_office = result[rec][3].seconds % 3600
            minutes_office = remaining_seconds_office // 60
            seconds_office = remaining_seconds_office % 60

            # Calculate total hours - Overtime Hours
            total_hours_overtime = result[rec][5].days * 24 + result[rec][5].seconds // 3600
            remaining_seconds_overtime = result[rec][5].seconds % 3600
            minutes_overtime = remaining_seconds_overtime // 60
            seconds_overtime = remaining_seconds_overtime % 60            

            # Calculate total hours - Final Total
            total_hours_all = result[rec][6].days * 24 + result[rec][6].seconds // 3600
            remaining_seconds_all = result[rec][6].seconds % 3600
            minutes_all = remaining_seconds_all // 60
            seconds_all = remaining_seconds_all % 60 



            self.create({
                'employee_id': result[rec][0],
                'employee_name': result[rec][0],
                'required_hours': f"{total_hours}:{minutes}:{seconds}",
                'remote_hours': f"{total_hours_remote}:{minutes_remote}:{seconds_remote}",
                'office_hours': f"{total_hours_office}:{minutes_office}:{seconds_office}",
                'excuses': result[rec][4],
                'overtime': f"{total_hours_overtime}:{minutes_overtime}:{seconds_overtime}",
                'total_hours': f"{total_hours_all}:{minutes_all}:{seconds_all}",
                'percentage': result[rec][7],
            })

        
        # Process `result` as needed, or display it in a view.
        # For example, you can create a report or display data in the wizard.

    #    self.create({
    #             'employee_id': result[rec][0],
    #             'employee_name': result[rec][0],
    #             'required_hours': datetime.strptime(str(result[rec][1]),'%H:%M:%S'), 
    #             'remote_hours': datetime.strptime(str(result[rec][2]),'%H:%M:%S'),
    #             'office_hours': datetime.strptime(str(result[rec][3]),'%H:%M:%S'),
    #             'excuses': datetime.strptime(str(result[rec][4]),'%H:%M:%S'),
    #             'overtime': datetime.strptime(str(result[rec][5]),'%H:%M:%S'),
    #             'total_hours': datetime.strptime(str(result[rec][6]),'%H:%M:%S'),
    #             'percentage': result[rec][7],
    #         })
