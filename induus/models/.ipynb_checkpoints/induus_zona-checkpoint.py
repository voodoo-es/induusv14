# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class Zona(models.Model):
    _name = "induus.zona"
    _description = "Zonas"

    name = fields.Char('Nombre', required=True)
    partner_ids = fields.One2many('res.partner', 'zona_id')
