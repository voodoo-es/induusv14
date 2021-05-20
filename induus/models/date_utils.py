# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import pytz
import logging

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields

_logger = logging.getLogger(__name__)

DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
DIAS_SEMANA_ONE_LETTER = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre',
         'Noviembre', 'Diciembre']

def timezone(self):
    return pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Europe/Madrid')

def date_range_month(fecha_inicio, fecha_fin):
    for n in range(int(diff_month(fecha_fin, fecha_inicio))):
        yield fecha_inicio + relativedelta(months=n)

def date_range(fecha_inicio, fecha_fin):
    for n in range(int((fecha_fin - fecha_inicio).days)):
        yield fecha_inicio + timedelta(n)

def sum_time_for_date(fecha, hora):
    tiempo = '{0:02.0f}:{1:02.0f}:00'.format(*divmod(hora * 60, 60)).split(":")
    return fecha + timedelta(hours=float(tiempo[0]), minutes=float(tiempo[1]))

def union_date_time(fecha, hora, tz):
    fecha_str = fecha.strftime("%Y-%m-%d")
    hora_str = time_float_to_str(hora)
    return tz.localize(fields.Datetime.from_string('%s %s' % (fecha_str, hora_str))).astimezone(pytz.timezone('UTC'))

def time_float_to_str(hora):
    return '{0:02.0f}:{1:02.0f}:00'.format(*divmod(hora * 60, 60))

def hora_float_desde_fecha(fecha, self):
    hora = display_date(fecha, "%H:%M", timezone(self)).split(":")
    return float(hora[0]) + (float(hora[1]) / 60)

def nombre_dia_semana(fecha):
    return DIAS_SEMANA[fecha.weekday()]

def letra_dia_semana(fecha):
    return DIAS_SEMANA_ONE_LETTER[fecha.weekday()]

def nombre_mes(fecha):
    return MESES[int(fecha.month)-1]

def diff_month(fecha_inicio, fecha_fin):
    return (fecha_inicio.year - fecha_fin.year) * 12 + fecha_inicio.month - fecha_fin.month

def display_date(fecha, format, self):
    return datetime.strftime(pytz.utc.localize(fecha).astimezone(timezone(self)), format)

def duracion_entre_fechas_float(fecha_inicio, fecha_fin):
    return (fecha_fin - fecha_inicio).total_seconds() / 3600

def dias_fin_semana(fecha_inicio, fecha_fin):
    dias_fin_semana = 0
    for fecha in date_range(fecha_inicio, fecha_fin):
        if fecha.weekday() >= 5:
            dias_fin_semana += 1
    return dias_fin_semana

# Esta función tambien es válida
# def display_date(fecha, record_user_timestamp):
#     timestamp = fields.Datetime.from_string(fecha)
#     ts = fields.Datetime.context_timestamp(record_user_timestamp, timestamp)
#     return pycompat.text_type(ts.strftime("%H:%M"))
