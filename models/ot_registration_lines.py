from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, time, timedelta
import pytz

class OtRegistrationLine(models.Model):
    _name = 'ot.registration.lines'

    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.employee_default())
    is_intern_contract = fields.Boolean('Is intern')
    project_id = fields.Many2one('project.project', string='Project', compute='_compute_project')
    date_from = fields.Datetime('Form', default=datetime.today())
    date_to = fields.Datetime('To', default=datetime.today())
    category = fields.Selection([('normal_day', 'Ngày bình thường'),
                                 ('normal_day_morning', 'OT ban ngày (6h-8h30)'),
                                 ('normal_day_night', 'Ngày bình thường - Ban đêm'),
                                 ('saturday', 'thứ 7'),
                                 ('sunday', 'chủ nhật'),
                                 ('week_day_night', 'ngày cuối tuần - Ban đêm'),
                                 ('holiday', 'ngày lễ'),
                                 ('holiday_night', 'ngày lễ - ban đêm'),
                                 ('compensatory_normal', 'Bù ngày lễ vào ngày thường'),
                                 ('compensatory_night', 'Bù ngày lễ vào ban đêm'),
                                 ('unknown', 'không thể xác định')], string='Category', compute='_compute_category')
    additional_hours = fields.Float('OT hours', compute='_compute_additional_hours', digits=(12, 0), default='0')
    job_taken = fields.Char('Job Taken', default='N/A')
    late_approved = fields.Boolean('Late approved', readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('to_approve', 'To Approve'),
                              ('approved', 'PM Approved'),
                              ('done', 'DL Approved'),
                              ('refused', 'Refused')], string='State', default='draft')
    is_wfh = fields.Boolean('WFH')
    ot_ids = fields.Many2one('ot.management', string='OT ID')
    notes = fields.Text('Note', readonly=True)
    attendance_notes = fields.Text('Attendance Notes', readonly=True)
    plan_hours = fields.Char('Warning', default='Exceed OT plan')

    def _compute_additional_hours(self):
        ots = self.env['ot.management'].sudo().search([])
        for rec in self:
            for ot in ots:
                if ot.employee_id.id == rec.employee_id.id:
                    rec.additional_hours = ot.additional_hours

    def _compute_project(self):
        ots = self.env['ot.management'].sudo().search([])
        for rec in self:
            for ot in ots:
                if ot.employee_id.id == rec.employee_id.id:
                    rec.project_id = ot.project_id

    def employee_default(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)], limit=1)


    @api.constrains('category')
    def update_state(self):
        for rec in self:
            if rec.category == 'unknown':
                raise ValidationError('Không thẻ tạo bản ghi')

    @api.depends('date_from', 'date_to')
    def _compute_category(self):
        for rec in self:
            start_day = time(8, 30, 0)
            end_day = time(22, 0, 0)
            time_to= rec.tz_utc_to_local(rec.date_to).time()
            time_from= rec.tz_utc_to_local(rec.date_from).time()
            time_to_week_night = time(22, 0, 0)
            time_from_week_night = time(6, 0, 0)
            start_day_normal = time(6, 0, 0)
            end_day_normal = time(8, 30, 0)
            start_day_normal_night = time(6, 0, 0)
            end_day_normal_night = time(8, 30, 0)

            if rec.date_from.weekday() == 5 and rec.date_to.weekday() == 5 and time_to >= start_day and time_from <= end_day:
                rec.category = 'saturday'
            elif rec.date_from.weekday() == 6 and rec.date_to.weekday() == 6 and time_to >= start_day and time_from<= end_day:
                rec.category = 'sunday'
            elif rec.date_from.weekday() == 6 and rec.date_to.weekday() == 7 and time_to >= time_to_week_night and time_from<=time_from_week_night:
                rec.category = 'week_day_night'
            elif rec.date_from.weekday() == 5 and rec.date_to.weekday() == 6 and time_to >= time_to_week_night and time_from<=time_from_week_night:
                rec.category = 'week_day_night'
            elif rec.date_from.weekday() != (5 or 6) and rec.date_to.weekday() != (5 or 6) and time_to >= start_day_normal and time_from <= end_day_normal:
                rec.category = 'normal_day_morning'
            elif rec.date_from.weekday() != (5 or 6) and rec.date_to.weekday() != (5 or 6) and time_to >= start_day_normal_night and time_from <= end_day_normal_night:
                rec.category = 'normal_day_night'
            else:
                rec.category = 'unknown'
    @api.model
    def tz_utc_to_local(self, utc_time):
        return utc_time + self.utc_offset()

    @api.model
    def tz_local_to_utc(self, local_time):
        return local_time - self.utc_offset()

    @api.model
    def utc_offset(self):
        user_timezone = self.env.user.tz or 'GMT'
        hours = int(datetime.now(pytz.timezone(user_timezone)).strftime('%z')[:3])
        return timedelta(hours=hours)
