from odoo import fields, models, api 


class EmpDocuments(models.Model):
    _name = 'emp.documents'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    file_content = fields.Binary(string="The Document")
    document_type = fields.Many2one('my_hr.documents', string="Document Type")

    machine_id = fields.Integer(compute="_compute_doc_machine_id")


    @api.depends('employee_id')
    def _compute_doc_machine_id(self):
        for record in self:
            record.machine_id = record.employee_id.machine_id