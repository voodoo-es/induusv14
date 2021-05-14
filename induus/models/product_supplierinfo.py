# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    multiplo = fields.Integer('Múltiplo', default=1)
