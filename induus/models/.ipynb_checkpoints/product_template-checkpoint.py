# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import babel
import dateutil.parser

# from odoo.addons.induus.models.induus_db import InduusDB
from odoo import models, fields, api, tools, _
from datetime import timedelta
from odoo.addons.induus.models import date_utils

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = "sequence, name, id"

    referencia_cliente_ids = fields.One2many('induus.referencia_cliente', 'product_tmpl_id')
    route_ids = fields.Many2many(default=lambda self: self._default_route_ids())
    sale_delay_with_stock = fields.Integer('Plazo de entrega del cliente (con stock)', default=2)
    imprimir_etiqueta_por_cantidad = fields.Boolean('Imprimir etiqueta por cantidad de productos', default=True,
                                                    help="Si es falso se imprimirá por línea")
    descripcion_website = fields.Text('Descripción web')
    categ_id = fields.Many2one('product.category', 'Product Category', default=None)
    creado_desde_tarifa = fields.Boolean("Creado desde tarifa")
    actualizado_desde_tarifa = fields.Boolean("Actualizado desde tarifa")

#     @api.multi
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        self.ensure_one()

        current_website = False

        if self.env.context.get('website_id'):
            current_website = self.env['website'].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()

        combination_info = super(ProductTemplate, self)._get_combination_info(combination, product_id, add_qty, pricelist, parent_combination, only_template)

        if self.env.context.get('website_id'):
            partner = self.env.user.partner_id
            company_id = current_website.company_id
            product = self.env['product.product'].browse(combination_info['product_id']) or self

            tax_display = 'total_included'
            taxes = partner.property_account_position_id.map_tax(
                product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id), product, partner)

            # The list_price is always the price of one.
            quantity_1 = 1
            price = taxes.compute_all(combination_info['price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            if pricelist.discount_policy == 'without_discount':
                list_price = taxes.compute_all(combination_info['list_price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            else:
                list_price = price
            has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1

            combination_info.update(
                price=price,
                list_price=list_price,
                has_discounted_price=has_discounted_price,
            )

        return combination_info

#     @api.model
#     def traer_mysql(self, offset, limit):
#         _logger.warning('----------- Actualizar Precio Producto (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM Graco_Carlissle where actualizado != 1 LIMIT %s" % limit)
#         for (referencia, precioVenta, precioCoste, actualizado) in data:
#             _logger.warning('Productos con Ref. Interna: %s' % referencia)
#             productos = self.search([('default_code', '=', referencia)])
#             productos.write({
#                 'list_price': precioVenta,
#                 'standard_price': precioCoste
#             })
#             InduusDB.update("UPDATE Graco_Carlissle SET actualizado = 1 where referencia='%s'" % referencia)

#     @api.model
#     def actualizar_añadir_precio_compra_LSO(self, offset, limit):
#         # No se contemplan variantes
#         # No se contemplan variantes
#         # No se contemplan variantes
#         _logger.warning('----------- Actualizar/Añadir Precio Compra Producto LSO (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM tarifaLSO where actualizado != 1 LIMIT %s" % limit)
#         for (referencia, categoriaId, precioCoste, descuento, descuento2, descuento3, proveedorId, plazoEntrega,actualizado) in data:
#             #Comprobar si existe la referencia-categoria como producto
#             producto = self.search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#             if producto:
#                 for producto_individual in producto:
#                     producto_proveedor = self.env['product.supplierinfo'].search([('product_tmpl_id','=',producto_individual.id),('name.id','=',proveedorId)], limit=1)
#                     if producto_proveedor:
#                         producto_proveedor.write({
#                                 'price': precioCoste,
#                                 'discount': descuento,
#                                 'discount2': descuento,
#                                 'discount3': descuento,
#                                 'delay' : plazoEntrega
#                             })
#                         _logger.warning('Producto con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     else:
#                         producto_proveedor.create({
#                                 'name' : proveedorId,
#                                 'product_tmpl_id' : producto_individual.id,
#                                 'price': precioCoste,
#                                 'discount': descuento,
#                                 'discount2': descuento,
#                                 'discount3': descuento,
#                                 'delay' : plazoEntrega
#                             })
#                         _logger.warning('Producto con Ref. Interna: %s creado precio de compra proveedor¡' % referencia)
#             InduusDB.update("UPDATE tarifaLSO SET actualizado = 1 where referencia='%s'" % referencia)

#     @api.model
#     def actualizar_compra_carlisle(self, offset, limit):
#         # tabla base de datos -> Carlisle19
#         # Estructura
#         # idExterno
#         # referenciaInterna
#         # nombreProveedor
#         # codigoProductoProveedor
#         # precioNetoProveedor
#         # plazoEntrega
#         # actualizado
#         _logger.warning('----------- Actualizar Precio Compra Producto (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM Carlisle19 where actualizado != 1 LIMIT %s" % limit)
#         for (idExterno, referenciaInterna, nombreProveedor, codigoProductoProveedor, precioNetoProveedor,plazoEntrega,actualizado) in data:
#             _logger.warning('Productos con Ref. Interna: %s' % referenciaInterna)
#             productosProveedor = self.env['product.supplierinfo'].search([('product_code', '=', codigoProductoProveedor)])
#             productosProveedor.write({
#                 'price': precioNetoProveedor,
#                 'delay': plazoEntrega
#             })
#             InduusDB.update("UPDATE Carlisle19 SET actualizado = 1 where idExterno='%s'" % idExterno)

#     @api.model
#     #Solo actualizamos precio de compra, tanto de producto como de proveedor
#     def actualizar_intrastat(self, offset, limit):
#         _logger.warning('----------- Actualizar desde mysql, limite (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM ProductosIntrastat where actualizado != 1 LIMIT %s" % limit)
#         for (referencia, categoriaId, commodityCode, peso, actualizado) in data:
#             producto = self.search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#             if producto:
#                 for producto_individual in producto:
#                     intrastat_id = self.env['account.intrastat.code'].search([('code', '=', commodityCode)], limit=1)
#                     if intrastat_id:
#                         producto_individual.write({
#                             'intrastat_id': intrastat_id.id,
#                             'weight' : peso
#                         })
#                         _logger.warning('Producto con Ref. Interna: %s actualizado intrastat y peso' % referencia)
#                     else:
#                         producto_individual.write({
#                             'weight' : peso
#                         })
#                         _logger.warning('Producto con Ref. Interna: %s actualizado peso' % referencia)
#             else:
#                 variante = self.env['product.product'].search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#                 if variante:
#                     intrastat_id = self.env['account.intrastat.code'].search([('code', '=', commodityCode)])
#                     if intrastat_id:
#                         variante.write({
#                             'intrastat_id': intrastat_id.id,
#                             'weight' : peso
#                         })
#                         _logger.warning('Variante con Ref. Interna: %s actualizada intrastat y peso' % referencia)
#                     else:
#                         variante.write({
#                             'weight' : peso
#                         })
#                         _logger.warning('Variante con Ref. Interna: %s actualizada peso' % referencia)
#             InduusDB.update("UPDATE ProductosIntrastat SET actualizado = 1 where referencia='%s'" % referencia)

#     @api.model
#     #Solo actualizamos precio de compra, tanto de producto como de proveedor
#     def actualizar_precios_compra_desde_mysql(self, offset, limit):
#         _logger.warning('----------- Actualizar desde mysql, limite (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM ProductosCompra where actualizado != 1 LIMIT %s" % limit)
#         for (referencia, categoriaId, precioCoste, proveedorId, actualizado) in data:
#             producto = self.search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#             if producto:
#                 for producto_individual in producto:
#                     for proveedor in producto_individual.seller_ids:
#                         if proveedor.name.id == proveedorId:
#                             proveedor.write({
#                                 'price': precioCoste,
#                             })
#                             producto_individual.write({
#                                 'standard_price': precioCoste,
#                             })
#                             _logger.warning('Producto con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     _logger.warning('Producto con Ref. Interna: %s actualizado¡' % referencia)
#             else:
#                 variante = self.env['product.product'].search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#                 if variante:
#                     proveedor_variante = self.env['product.supplierinfo'].search([('product_id','=',variante.id)])
#                     for proveedor in proveedor_variante:
#                         if proveedor.name.id == proveedorId:
#                             proveedor.write({
#                                 'price': precioCoste,
#                             })
#                             variante.write({
#                                 'standard_price': precioCoste
#                             })
#                             _logger.warning('Variante con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     _logger.warning('Variante con Ref. Interna: %s actualizado¡' % referencia)
#             InduusDB.update("UPDATE ProductosCompra SET actualizado = 1 where referencia='%s'" % referencia)

#     @api.model
#     #Solo actualizamos productos, nunca creamos
#     def actualizar_productos_desde_mysql(self, offset, limit):
#         _logger.warning('----------- Actualizar desde mysql, limite (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM Productos where actualizado != 1 LIMIT %s" % limit)
#         for (referencia, descripcion, categoriaId, precioVenta, precioCoste, proveedorId, actualizado) in data:
#             producto = self.search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#             if producto:
#                 for producto_individual in producto:
#                     movimientos = self.env['stock.move.line'].search([('product_id','=',producto_individual.product_variant_id.id)])
#                     if movimientos:
#                         producto_individual.write({
#                             'list_price': precioVenta,
#                         })
#                     else:
#                         producto_individual.write({
#                             'list_price': precioVenta,
#                             'standard_price': precioCoste,
#                         })
#                     for proveedor in producto_individual.seller_ids:
#                         if proveedor.name.id == proveedorId:
#                             proveedor.write({
#                                 'price': precioCoste,
#                             })
#                             _logger.warning('Producto con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     _logger.warning('Producto con Ref. Interna: %s actualizado¡' % referencia)
#             else:
#                 variante = self.env['product.product'].search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#                 if variante:
#                     movimientos = self.env['stock.move.line'].search([('product_id','=',variante.id)])
#                     if movimientos:
#                         variante.write({
#                             'list_price': precioVenta,
#                             'lst_price': precioVenta,
#                             'fix_price': precioVenta
#                         })
#                     else:
#                         variante.write({
#                             'list_price': precioVenta,
#                             'lst_price': precioVenta,
#                             'fix_price': precioVenta,
#                             'standard_price': precioCoste
#                         })
#                     proveedor_variante = self.env['product.supplierinfo'].search([('product_id','=',variante.id)])
#                     for proveedor in proveedor_variante:
#                         if proveedor.name.id == proveedorId:
#                             proveedor.write({
#                                 'price': precioCoste,
#                             })
#                             _logger.warning('Variante con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     _logger.warning('Variante con Ref. Interna: %s actualizado¡' % referencia)
#             InduusDB.update("UPDATE Productos SET actualizado = 1 where referencia='%s'" % referencia)

#     @api.model
#      #Actualizamos productos, si no existen los creamos
#     def actualizar_crear_productos_desde_mysql(self, offset, limit):
#         _logger.warning('----------- Actualizar desde mysql, limite (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM Productos where actualizado != 1 LIMIT %s" % limit)
#         for (referencia, descripcion, categoriaId, precioVenta, precioCoste, proveedorId, actualizado) in data:
#             producto = self.search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#             if producto:
#                 for producto_individual in producto:
#                     movimientos = self.env['stock.move.line'].search([('product_id','=',producto_individual.product_variant_id.id)])
#                     if movimientos:
#                         producto_individual.write({
#                             'list_price': precioVenta,
#                         })
#                     else:
#                         producto_individual.write({
#                             'list_price': precioVenta,
#                             'standard_price': precioCoste,
#                         })
#                     for proveedor in producto_individual.seller_ids:
#                         if proveedor.name.id == proveedorId:
#                             proveedor.write({
#                                 'price': precioCoste,
#                             })
#                             _logger.warning('Producto con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     _logger.warning('Producto con Ref. Interna: %s actualizado¡' % referencia)
#             else:
#                 variante = self.env['product.product'].search([('default_code', '=', referencia),('categ_id','=',categoriaId)])
#                 if variante:
#                     movimientos = self.env['stock.move.line'].search([('product_id','=',variante.id)])
#                     if movimientos:
#                         variante.write({
#                             'list_price': precioVenta,
#                             'lst_price': precioVenta,
#                             'fix_price': precioVenta
#                         })
#                     else:
#                         variante.write({
#                             'list_price': precioVenta,
#                             'lst_price': precioVenta,
#                             'fix_price': precioVenta,
#                             'standard_price': precioCoste
#                         })
#                     proveedor_variante = self.env['product.supplierinfo'].search([('product_id','=',variante.id)])
#                     for proveedor in proveedor_variante:
#                         if proveedor.name.id == proveedorId:
#                             proveedor.write({
#                                 'price': precioCoste,
#                             })
#                             _logger.warning('Variante con Ref. Interna: %s actualizado precio de compra proveedor¡' % referencia)
#                     _logger.warning('Variante con Ref. Interna: %s actualizado¡' % referencia)
#                 else:
#                     idProducto = producto.create({
#                         'name' : descripcion,
#                         'default_code' : referencia,
#                         'type' : 'product',
#                         'categ_id' : categoriaId,
#                         'list_price' : precioVenta,
#                         'standard_price': precioCoste,
#                         'invoice_policy' : 'delivery',
#                         'purchase_method' : 'receive',
#                         'sale_delay' : 7,
#                         'route_ids' : [(6,0,[5,12])],
#                         'taxes_id' : [(6,0,[1])],
#                         'supplier_taxes_id' : [(6,0,[4])]
#                         })
#                     if proveedorId:
#                         productoProveedor = self.env['product.supplierinfo']
#                         productoProveedor.create({
#                             'name' : proveedorId,
#                             'product_name' : descripcion,
#                             'product_code' : referencia,
#                             'price' : precioCoste,
#                             'product_tmpl_id' : idProducto.id,
#                             'delay': 5
#                             })
#                     _logger.warning('Producto con Ref. Interna: %s creado¡' % referencia)
#             InduusDB.update("UPDATE Productos SET actualizado = 1 where referencia='%s'" % referencia)

#     @api.model
#     def actualizar_graco_mysql(self, offset, limit):
#         _logger.warning('----------- Actualizar graco2021 desde mysql, limite (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM Graco2021 where actualizado != 1 LIMIT %s" % limit)
#         referencias = []
#         for (referencia, descripcion, venta, compra, actualizado) in data:
#             productos = self.search([
#                 ('default_code', '=', referencia),
#                 ('categ_id','in', [139, 7, 151, 127, 163, 142, 140, 145, 143, 147, 144, 146, 141, 148, 149,
#                                   154, 152, 157, 155, 159, 156, 158, 153, 160, 161, 130, 128, 133, 131, 135,
#                                   132, 134, 129, 136, 137, 166, 164, 169, 167, 171, 168, 170, 165, 172, 173]),
#             ])
            
#             values = {
#                 'list_price': venta,
#                 'standard_price': compra,
#                 'name': descripcion
#             }
            
#             if productos:
#                 values.update({'actualizado_desde_tarifa': True})
#                 productos.write(values)
#                 for producto in productos:
#                     producto.seller_ids.write({'price': compra,})
#             else:
#                 values.update({
#                     'default_code': referencia,
#                     'categ_id': 7,
#                     'creado_desde_tarifa': True
#                 })
#                 self.create(values)
                
#             referencias.append(referencia)
            
#             if referencias:
#                 referencias_txt = ""
#                 for referencia in referencias:
#                     referencias_txt += "," if referencias_txt else "("
#                     referencias_txt = "%s'%s'" % (referencias_txt, referencia)
#                 referencias_txt = "%s)" % referencias_txt
#                 InduusDB.update("UPDATE Graco2021 SET actualizado = 1 where referencia IN %s" % referencias_txt)
            
#     @api.model
#     def actualizar_carlisle_mysql(self, offset, limit):
#         _logger.warning('----------- Actualizar Carlisle2021 desde mysql, limite (%s)---------------' % limit)
#         data = InduusDB.select("SELECT * FROM Carlisle2021 where actualizado != 1 LIMIT %s" % limit)
#         referencias = []
#         for (referencia, descripcion, venta, compra, commodity_code, peso, actualizado) in data:
#             productos = self.search([
#                 ('default_code', '=', str(referencia)),
#                 ('categ_id','in', [186, 8, 188, 187, 189]),
#             ])
#             values = {
#                 'list_price': venta,
#                 'standard_price': compra,
#                 'name': descripcion,
#                 'weight': peso,
#             }
            
#             account_intrastat = self.env['account.intrastat.code'].search([('code', '=', commodity_code)], limit=1)
#             if account_intrastat:
#                 values.update({'intrastat_id': account_intrastat.id})
            
#             if productos:
#                 values.update({'actualizado_desde_tarifa': True})
#                 productos.write(values)
#                 for producto in productos:
#                     producto.seller_ids.write({'price': compra})
#             else:
#                 values.update({
#                     'default_code': referencia,
#                     'categ_id': 8,
#                     'creado_desde_tarifa': True
#                 })
#                 self.create(values)
#             referencias.append(referencia)
        
#         if referencias:
#             referencias_txt = ""
#             for referencia in referencias:
#                 referencias_txt += "," if referencias_txt else "("
#                 referencias_txt = "%s'%s'" % (referencias_txt, referencia)
#             referencias_txt = "%s)" % referencias_txt
#             InduusDB.update("UPDATE Carlisle2021 SET actualizado=1 where referencia IN %s" % referencias_txt)
            
    def referencia_cliente(self, partner):
        self.ensure_one()
        domain = [('product_tmpl_id', '=', self.id)]
        if partner.parent_id:
            domain += ['|',
                ('partner_id', '=', partner.id),
                ('partner_id', '=', partner.parent_id.id),
            ]
        else:
            domain += [('partner_id', '=', partner.id)]

        referencias = self.env['induus.referencia_cliente'].search(domain)
        refs_cliente = list(set([r.name for r in referencias]))
        return ', '.join(refs_cliente)

    @api.model
    def _default_route_ids(self):
        routes = []
#         route = self.env.ref('stock_mts_mto_rule.route_mto_mts')
#         if route: routes.append(route.id)

        route = self.env.ref('purchase_stock.route_warehouse0_buy')
        if route: routes.append(route.id)

        return routes

    def delay_website(self, cantidad=1, format="string", code_pais="ES"):
        self = self.sudo()
        if not code_pais:
            code_pais = "ES"

        if self.product_variant_count <= 1:
            return self.product_variant_id.delay_website(cantidad, format, code_pais)

        FechaFestivo = self.env['induus.fecha_festivo']
        locale = self.env.context.get('lang') or 'en_US'

        def return_fecha(fecha, format, code_pais):
            if code_pais != 'ES':  # para envios fuera de españa sumamos 3 días
                fecha += timedelta(days=3)

            dias_festivos = FechaFestivo.dias_festivos_y_findes(fields.Datetime.now(), fecha)
            if dias_festivos:
                fecha += timedelta(days=dias_festivos)

            if format == 'string':
                return _("Fecha prevista de entrega: a partir del ") + tools.ustr(babel.dates.format_date(date=fecha, format='full', locale=locale))
            elif format == 'days':
                return (dateutil.parser.parse(fields.Datetime.to_string(fecha)).date() - fields.Date.today()).days
            else:
                return fecha

        if cantidad <= 0 or self.qty_available < cantidad:
            dias = int(self.sale_delay)
            if dias <= 0:
                return None
            fecha = fields.Datetime.now() + timedelta(days=dias)
            return return_fecha(fecha, format, code_pais)

        if int(date_utils.display_date(fields.Datetime.now(), '%H', self)) < 12:
            fecha = fields.Datetime.now() + timedelta(days=1)
            return return_fecha(fecha, format, code_pais)

        fecha = fields.Datetime.now() + timedelta(days=self.sale_delay_with_stock)
        return return_fecha(fecha, format, code_pais)

    def print_date_website(self, days):
        locale = self.env.context.get('lang') or 'en_US'
        fecha = fields.Datetime.now() + timedelta(days=days)
        return _("Fecha prevista de entrega: a partir del ") + tools.ustr(
            babel.dates.format_date(date=fecha, format='full', locale=locale))
