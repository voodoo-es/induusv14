# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
from email.utils import getaddresses

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Team(models.Model):
    _inherit = 'crm.team'

    sale_order_partner_ids = fields.One2many('res.partner', 'sale_order_team_id',
                                             string="Contactos de Pedidos de venta")
