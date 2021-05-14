# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderLost(models.TransientModel):
    _name = 'sale.order.lost'
    _description = 'Obtener motivo de cancelación'

    lost_reason_id = fields.Many2one('sale.order.lost.reason', 'Motivo de cancelación')

#     @api.multi
    def action_lost_reason_apply(self):
        order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        order.write({'lost_reason': self.lost_reason_id.id})
        return order.action_set_lost()
