# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class RefrenciaCliente(models.Model):
    _name = "induus.referencia_cliente"
    _description = "Referencias Cliente"

    name = fields.Char('Referencia', required=True)
    product_tmpl_id = fields.Many2one('product.template', string="Producto")
    partner_id = fields.Many2one('res.partner', string="Cliente")
