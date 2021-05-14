# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Followers(models.Model):
    _inherit = 'mail.followers'

    def _add_followers(self, res_model, res_ids, partner_ids, partner_subtypes, channel_ids, channel_subtypes,
                       check_existing=False, existing_policy='skip'):
        new, update = super(Followers, self)._add_followers(res_model, res_ids, partner_ids, partner_subtypes, channel_ids,
                                                     channel_subtypes, check_existing, existing_policy)

        if res_model == 'account.move':
            for key in new:
                new[key] = []

        return new, update
