from odoo import models, api, fields

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

    percentage = fields.Char(
        string='Percentage'
    )


    def calculate_report(self):
        query = """
            SELECT 
    employee_id,
    (SELECT name_ar 
     FROM hr_employee 
     WHERE hr_employee.id = a.employee_id) AS ar_name,
    -- Required hours calculation
    ((((SELECT 
        count(*) - 1 
    	FROM 
        generate_series('2024-10-01'::date, '2024-10-30'::date, '1 day'::interval) AS date
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
		BETWEEN '2024-10-01' AND '2024-10-30' AND leave_dates.employee_id = a.employee_id
		GROUP BY employee_id) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)
			),interval '0 hours'))-
			(SELECT 
    ((COALESCE((CASE 
                WHEN Date_start - '2024-10-01' > 0 AND Date_start - '2024-10-01' < 30 
                THEN Date_start - '2024-10-01' 
                ELSE 0 
              END), 0) 
     + 
     COALESCE((CASE 
                WHEN '2024-10-30' - date_end > 0 AND '2024-10-30' - date_end < 30 
                THEN '2024-10-30' - date_end 
                ELSE 0 
              END), 0)) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)) AS total_hours
		FROM hr_contract where hr_contract.employee_id = a.employee_id )) AS req_hours,
     
    COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) 
     FROM hr_attendance b 
     WHERE a.employee_id = b.employee_id 
       AND remote = TRUE 
       AND check_in BETWEEN '2024-10-01' AND '2024-10-30'),0) * interval '1 hour' AS Remote_Hours,
       
    (SELECT SUM(COALESCE(worked_hours, 0)) 
     FROM hr_attendance b 
     WHERE a.employee_id = b.employee_id 
       AND remote = FALSE 
       AND check_in BETWEEN '2024-10-01' AND '2024-10-30') * interval '1 hour' AS Office_Hours,
       
    SUM(COALESCE((SELECT number_of_days * interval '1 hours' 
                  FROM hr_leave 
                  WHERE holiday_status_id = 11 
                    AND hr_leave.employee_id = a.employee_id 
                    AND hr_leave.request_date_from  BETWEEN '2024-10-01' AND '2024-10-30'
				    AND hr_leave.state = 'validate'
                    LIMIT 1), interval '0 hours') )  AS Ex,
                  
    (SELECT SUM(COALESCE(overtime_hours, 0)) 
     FROM hr_attendance b 
     WHERE check_in BETWEEN '2024-10-01' AND '2024-10-30' 
     AND a.employee_id = b.employee_id) * interval '1 hour' AS OVR,
       
    -- Total Hours calculation
    (
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = TRUE 
                    AND check_in BETWEEN '2024-10-01' AND '2024-10-30'), interval '0 hours') + 
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = FALSE 
                    AND check_in BETWEEN '2024-10-01' AND '2024-10-30'), interval '0 hours') + 
        COALESCE(SUM(COALESCE((SELECT number_of_days * interval '1 hours'
                               FROM hr_leave 
                               WHERE holiday_status_id = 11 
                                 AND hr_leave.employee_id = a.employee_id 
                                 AND hr_leave.request_date_from BETWEEN '2024-10-01' AND '2024-10-30'
                                 AND hr_leave.state = 'validate'
                               LIMIT 1), interval '0 hours')), interval '0 hours')
    ) AS total_hours,

    -- Total Hours formatted
    TO_CHAR(
    (
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = TRUE 
                    AND check_in BETWEEN '2024-10-01' AND '2024-10-30'), interval '0 hours') + 
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = FALSE 
                    AND check_in BETWEEN '2024-10-01' AND '2024-10-30'), interval '0 hours') + 
        COALESCE(SUM(COALESCE((SELECT number_of_days * interval '1 hours'
                               FROM hr_leave 
                               WHERE holiday_status_id = 11 
                                 AND hr_leave.employee_id = a.employee_id 
                                 AND hr_leave.request_date_from BETWEEN '2024-10-01' AND '2024-10-30'
                                 AND hr_leave.state = 'validate'
                               LIMIT 1), interval '0 hours')), interval '0 hours')
    ),
    'HH24:MI:SS'
) AS total_hours_formatted,

    -- Percentage calculation using inline req_hours calculation with FLOOR applied
    FLOOR((EXTRACT(EPOCH FROM (
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = TRUE 
                    AND check_in BETWEEN '2024-10-01' AND '2024-10-30'), interval '0 hours') + 
        COALESCE((SELECT SUM(COALESCE(worked_hours, 0)) * interval '1 hour'
                  FROM hr_attendance b 
                  WHERE a.employee_id = b.employee_id 
                    AND remote = FALSE 
                    AND check_in BETWEEN '2024-10-01' AND '2024-10-30'), interval '0 hours') + 
        COALESCE(SUM(COALESCE((SELECT number_of_days * interval '1 hours'
                               FROM hr_leave 
                               WHERE holiday_status_id = 11 
                                 AND hr_leave.employee_id = a.employee_id 
                                 AND hr_leave.request_date_from BETWEEN '2024-10-01' AND '2024-10-30'
                                 AND hr_leave.state = 'validate'
                               LIMIT 1), interval '0 hours')), interval '0 hours')
    )) / EXTRACT(EPOCH FROM ((((SELECT 
        count(*) - 1 
    	FROM 
        generate_series('2024-10-01'::date, '2024-10-30'::date, '1 day'::interval) AS date
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
		BETWEEN '2024-10-01' AND '2024-10-30' AND leave_dates.employee_id = a.employee_id
		GROUP BY employee_id) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)
			),interval '0 hours'))-
			(SELECT 
    ((COALESCE((CASE 
                WHEN Date_start - '2024-10-01' > 0 AND Date_start - '2024-10-01' < 30 
                THEN Date_start - '2024-10-01' 
                ELSE 0 
              END), 0) 
     + 
     COALESCE((CASE 
                WHEN '2024-10-30' - date_end > 0 AND '2024-10-30' - date_end < 30 
                THEN '2024-10-30' - date_end 
                ELSE 0 
              END), 0)) * ( case when employee_id in (7,11) then interval '6:45 hour' else  interval '7:45 hour' end)) AS total_hours
		FROM hr_contract where hr_contract.employee_id = a.employee_id )))) * 100) AS percentage

FROM hr_attendance a 
WHERE check_in BETWEEN '2024-10-01' AND '2024-10-30'
GROUP BY employee_id;

        """
        # self.env.cr.execute(query, (self.start_date, self.end_date))
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()

        # raise UserError('dataaaaaaaaaaaaaaa ' + str(result))


        get_length = len(result)

        for rec in range(get_length):

            self.create({
                'employee_id': result[rec][0],
                'employee_name': result[rec][0],
                'required_hours': result[rec][2],
                'remote_hours': result[rec][3],
                'office_hours': result[rec][4],
                'excuses': result[rec][5],
                'overtime': result[rec][6],
                'total_hours': result[rec][7],
                'percentage': result[rec][8],
            })

        
        # Process `result` as needed, or display it in a view.
        # For example, you can create a report or display data in the wizard.

    