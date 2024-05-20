from odoo import fields, models, api 



class AttEffects(models.Model):
    _name = 'att.effects'

    employee_id = fields.Many2one('hr.employee', string="EmployeeID", required=True, ondelete='cascade')
    effect_type = fields.Selection(selection=[
        ('att', 'Attendance'),
        ('earlyleave', 'Early Leave'),
        ('lateatt', 'Late Attendance'),
        ('timeoff(days)', 'TimeOff(Days)'),
        ('timeoff(hours)', 'TimeOff(Hours)'),
        ('absence', 'Absence'),
        ('overtime', 'Over Time'),
        ('extradays', 'Extra Days'),
        ('shortage', 'Shortage')
    ], string="Effect Type")

    date_from = fields.Datetime(string="Date From", required=True)
    date_to = fields.Datetime(string="Date To", required=True)
    hours = fields.Float(string="Hours")
    minutes = fields.Float(string="Minutes")
    description = fields.Char(string='Description', required=False)
    att_machine_id = fields.Integer(compute="_compute_machine_id", store=True)


    @api.depends('employee_id')
    def _compute_machine_id(self):
        for eff in self:
            employee = self.env['hr.employee'].search([('id', '=', eff.employee_id.id)], limit=1)
            eff.att_machine_id = employee.machine_id if employee else False




