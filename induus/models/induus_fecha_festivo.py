# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api, _
from odoo.addons.induus.models import date_utils
from datetime import timedelta

_logger = logging.getLogger(__name__)


class FechaFestivo(models.Model):
    _name = "induus.fecha_festivo"
    _description = "Días festivos"

    name = fields.Date('Fecha', required=True, unique=True)

    _sql_constraints = [('name_uniq', 'unique (name)', "La fecha ya existe."),]

    @api.model
    def dias_festivos(self, fecha_inicio, fecha_fin):
        dias = 0
        for fecha in date_utils.date_range(fecha_inicio, fecha_fin):
            dia = self.search([('name', '=', fecha)], limit=1)
            if dia:
                dias += 1
        return dias

    @api.model
    def dias_festivos_y_findes(self, fecha_inicio, fecha_fin):
        dias = 0
        for fecha in date_utils.date_range(fecha_inicio, fecha_fin + timedelta(days=1)):
            if fecha.weekday() >= 5:
                dias += 1
                continue

            dia = self.search([('name', '=', fecha)], limit=1)
            if dia:
                dias += 1

        while True:
            fecha = fecha_fin + timedelta(days=dias)
            if fecha.weekday() >= 5:
                dias += 1
                continue

            es_festivo = self.search([('name', '=', fecha)], limit=1)
            if es_festivo:
                dias += 1
                continue
            break

        return dias
