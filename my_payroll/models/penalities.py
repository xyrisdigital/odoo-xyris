from odoo import fields, models, api 


class Violations(models.Model):
    _name = 'payroll.violations'

    name = fields.Char(string="Penality", required=True)
    late_attendance = fields.Float(string="Late Attendance")
    early_departure = fields.Float(string="Early Departure")
    first = fields.Float(string="First")
    second = fields.Float(string="Second")
    third = fields.Float(string="Third")
    fourth = fields.Float(string="Fourth")
    more = fields.Float(string="More")

