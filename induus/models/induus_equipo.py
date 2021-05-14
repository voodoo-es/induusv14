# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Equipo(models.Model):
    _name = "induus.equipo"
    _description = "Equipo"

    codigo_induus = fields.Char(string="Código Induus", required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    name = fields.Char(string="Equipo", required=True)
    descripcion = fields.Char('Descripción', required=True)
    serie = fields.Char('Serie', required=True)
    referencia = fields.Char('Referencia', required=True)
    serial = fields.Char('Serial', required=True)
    eme = fields.Char('EME', required=True)
    sale_order_ids = fields.One2many('sale.order', 'equipo_id', string="Ventas")
    partner_id = fields.Many2one('res.partner', domain="[('customer', '=', True)]", string="Cliente")

    @api.model
    def create(self, vals):
        if vals.get('codigo_induus', _('New')) == _('New'):
            vals['codigo_induus'] = self.env['ir.sequence'].next_by_code('induus.equipo') or _('New')
        result = super(Equipo, self).create(vals)
        return result
