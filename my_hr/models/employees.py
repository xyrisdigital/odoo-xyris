from odoo import models, fields, api

class MyEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    machine_id = fields.Integer(required=True, copy=False, default=None, tracking=True)



    _sql_constraints = [
        ('UniqueEmpID', 'unique(machine_id)', 'Sorry, but the employee ID must be unique')
    ]


 

class MyCustomEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'


    name_ar = fields.Char(string="الإسم")
    title_ar = fields.Char(related="job_id.name_ar")

    emp_documents = fields.Many2many('ir.attachment', string="Hiring Documents", help='Please attach Documents', copy=False)
    
        



class MyCustomJobs(models.Model):
    _inherit = 'hr.job'

    name_ar = fields.Char(string="اسم الوظيفه", required=True)
    
