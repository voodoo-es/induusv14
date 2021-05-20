# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

#     @api.multi
    def action_feedback_schedule_next(self, feedback=False):
        ctx = dict(
            clean_context(self.env.context),
            default_previous_activity_type_id=self.activity_type_id.id,
            activity_previous_deadline=self.date_deadline,
            default_res_id=self.res_id,
            default_res_model=self.res_model,
            default_user_id=self.user_id.id
        )
        force_next = self.force_next
        self.action_feedback(feedback)  # will unlink activity, dont access self after that
        if force_next:
            Activity = self.env['mail.activity'].with_context(ctx)
            res = Activity.new(Activity.default_get(Activity.fields_get()))
            res._onchange_previous_activity_type_id()
            res._onchange_activity_type_id()
            activity = Activity.create(res._convert_to_write(res._cache))
            return False
        else:
            return {
                'name': _('Schedule an Activity'),
                'context': ctx,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.activity',
                'views': [(False, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    seguimiento_cliente = fields.Boolean('Seguimiento Cliente')
    seguimiento_comercial = fields.Boolean('Seguimiento Comercial')
