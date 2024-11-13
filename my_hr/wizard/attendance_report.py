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

        self.env['att.report'].sudo().search([]).unlink()

        # Run your SQL query
        get_function = self.env['att.report'].sudo().search([])

        get_function.calculate_report(self.public_days, self.start_date, self.end_date)

        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

        return {
            'type': 'ir.actions.act_url',
            'url': 'https://erp.xyrisdigital.com/web#action=611&model=att.report&view_type=list&cids=1&menu_id=401',
            # 'target': 'self',  # Options: 'self' for the same window, 'new' for a new tab
            'tag': 'reload',
        }

        