# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Mail(models.Model):
    _inherit = 'mail.mail'

#     @api.multi
    def write(self, vals):
        res = super(Mail, self).write(vals)
        # if vals.get('state') in ['exception', 'sent']:
        #     self.emails_fallidos()
        return res

#     @api.multi
    def emails_fallidos(self):
        for r in self.filtered(lambda x: x.model in ['sale.order', 'purchase.order', 'account.move']):
            res_model_id = self.env['ir.model'].sudo().search([('model', '=', r.model)], limit=1).id
            if r.state == 'exception' and r.failure_reason:
                record = self.env[r.model].browse(r.res_id)
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('induus.mail_act_fail_email').id,
                    'summary': "Email fallido",
                    'date_deadline': datetime.today(),
                    'user_id': record.user_id.id if record and record.user_id else 2,
                    'res_model': r.model,
                    'res_model_id': res_model_id,
                    'res_id': r.res_id,
                })

            if r.state == 'sent':
                mails = self.env['mail.activity'].search([
                    ('activity_type_id', '=', self.env.ref('induus.mail_act_fail_email').id),
                    ('res_id', '=', r.res_id),
                    ('res_model', '=', r.model),
                    ('res_model_id', '=', res_model_id),
                ])
                if mails:
                    mails.unlink()
