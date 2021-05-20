# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo import tools

_logger = logging.getLogger(__name__)

class InduusVentasProducto(models.Model):
    _name = "induus.ventas.producto"
    _description = "Ventas Producto"
    _auto = False

    referencia = fields.Char(string="Referencia")
    nombre = fields.Char(string="Producto")
    categoria = fields.Char(string='Categoria')
    pedido = fields.Char(string="Pedido")
    fecha = fields.Datetime(string="Fecha")
    cliente = fields.Char(string="Cliente")
    cliente_padre = fields.Char(string="Comprañia del cliente")
    cantidad = fields.Float(string="Cantidad")
    precio = fields.Float(string="Precio venta")
    costo = fields.Float(string="Precio coste")
    costo_actual = fields.Float(string="Precio compra actual")

#     @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW induus_ventas_producto AS (
                select
                    lineapedidoventa.id as id,
                    producto.default_code as referencia,
                    productoplantilla.name as nombre,
                    categoria.complete_name as categoria,
                    pedidoventa.name as pedido,
                    pedidoventa.date_order as fecha,
                    cliente.name as cliente,
                    clientepadre.name as cliente_padre,
                    lineapedidoventa.qty_delivered as cantidad,
                    lineapedidoventa.price_reduce as precio,
                    lineapedidoventa.purchase_price as costo,
                    proveedor.price as costo_actual
                from sale_order_line as lineapedidoventa
                    join sale_order as pedidoventa on lineapedidoventa.order_id=pedidoventa.id
                    join res_partner as cliente on pedidoventa.partner_id=cliente.id
                    left join res_partner as clientepadre on cliente.parent_id=clientepadre.id
                    left join product_product as producto on lineapedidoventa.product_id=producto.id
                    left join product_template as productoplantilla on producto.product_tmpl_id=productoplantilla.id
                    left join product_supplierinfo as proveedor on proveedor.id=(select bb.id
                        from product_supplierinfo bb
                        where productoplantilla.id = bb.product_tmpl_id
                        ORDER BY bb.product_tmpl_id
                        limit 1)
                    left join product_category as categoria on productoplantilla.categ_id=categoria.id
                where
                    pedidoventa.state != 'draft'
                    and pedidoventa.state != 'sent'
                    and pedidoventa.state != 'cancel'
       )""")
