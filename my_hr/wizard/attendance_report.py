from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class ReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Attendance Report'

    public_days = fields.Integer(string="Public Holyday Days", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def action_generate_report(self):
        # Validate dates if necessary
        # if self.start_date >= self.end_date:
        #     raise models.ValidationError("Start date must be earlier than the end date.")

        # Run your SQL query
        get_function = self.env['att.report'].sudo().search([])

        get_function.calculate_report()