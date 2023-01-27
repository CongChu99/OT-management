from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError


class OtManagement(models.Model):
    _name = "ot.management"

    project_id = fields.Many2one('project.project', string='Project', required=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', required=True)
    ot_month = fields.Char(string='OT Month', compute='_compute_ot_month', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, default=lambda self: self.employee_default())
    dl_manager_id = fields.Many2one('hr.employee', string='Department lead', default=lambda self: self.employee_default_dl(), readonly=True)
    create_date = fields.Datetime('Create Date', readonly=True)
    additional_hours = fields.Float('OT hours', compute='_compute_additional_hours', digits=(12, 0), default='0', store=True)
    ot_lines = fields.One2many('ot.registration.lines', 'ot_ids', string='OT Lines')
    state = fields.Selection([('draft', 'Draft'),
                              ('to_approve', 'To Approve'),
                              ('approved', 'PM Approved'),
                              ('done', 'DL Approved'),
                              ('refused', 'Refused')], string='State', default='draft', readonly=True)

    @api.depends('ot_lines.date_from')
    def _compute_ot_month(self):
        for rec in self:
            for line in rec.ot_lines:
                rec.ot_month = line.date_from.date().strftime('%m/%Y')

    @api.depends('ot_lines.date_from', 'ot_lines.date_to')
    def _compute_additional_hours(self):
        for rec in self:
            for line in rec.ot_lines:
                date_from = line.date_from.date()
                date_to = line.date_to.date()
                hour_from = line.date_from.hour
                hour_to = line.date_to.hour
                total = date_to - date_from
                hour1 = total.days*24 + (hour_to - hour_from)
                rec.additional_hours = hour1

    def employee_default(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)], limit=1)

    def action_submit(self):
        for rec in self:
            rec.state = 'to_approve'
            mail_template = self.env.ref('ot_management.email_template_pm_approved')
            mail_template.send_mail(self.id, force_send=True)

    def draft_request(self):
        for rec in self:
            rec.state = 'draft'

    def refuse_request_pm(self):
        for rec in self:
            rec.state = 'refused'
            mail_template = self.env.ref('ot_management.email_template_refuse_pm')
            mail_template.send_mail(self.id, force_send=True)

    def refuse_request_dl(self):
        for rec in self:
            rec.state = 'refused'
            mail_template = self.env.ref('ot_management.email_template_refuse_dl')
            mail_template.send_mail(self.id, force_send=True)

    def button_pm_dl_approve(self):
        for rec in self:
            rec.state = 'approved'
            mail_template = self.env.ref('ot_management.email_template_dl_approved')
            mail_template.send_mail(self.id, force_send=True)

    def button_dl_approve(self):
        for rec in self:
            rec.state = 'done'
            mail_template = self.env.ref('ot_management.email_template_done')
            mail_template.send_mail(self.id, force_send=True)

    def employee_default_dl(self):
        return self.env.ref('ot_management.hr_employee_dl_data').id

    @api.onchange('project_id')
    def management_pm(self):
        employees = self.env['hr.employee'].sudo().search([])
        for employee in employees:
            if self.project_id.user_id == employee.user_id:
                self.manager_id = employee.id

    def get_link(self):
        base_url = 'https://www.google.com.vn/?hl=vi'
        return base_url

    @api.constrains('additional_hours')
    def check_create(self):
        for rec in self:
            print(rec.additional_hours)
            if rec.additional_hours == 0:
                raise ValidationError('can nhap OT')