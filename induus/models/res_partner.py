# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from email.utils import getaddresses

_logger = logging.getLogger(__name__)

CAMPOS_OBLIGATORIOS_EMPRESA = ['street_name', 'city', 'state_id', 'zip', 'country_id', 'phone', 'email', 'vat',
                               'category_id']
CAMPOS_OBLIGATORIOS_EMPRESA_CLIENTE = ['zona_id', 'comercial']
CAMPOS_OBLIGATORIOS_EMPRESA_PROVEEDOR = ['comercial']
CAMPOS_OBLIGATORIOS_CLIENTE = ['property_product_pricelist', 'property_payment_term_id', 'customer_payment_mode_id', 'property_account_position_id']
CAMPOS_OBLIGATORIOS_PROVEEDOR = ['property_supplier_payment_term_id', 'supplier_payment_mode_id', 'property_account_position_id']


class Partner(models.Model):
    _inherit = 'res.partner'

    referencia_cliente_ids = fields.One2many('induus.referencia_cliente', 'partner_id')
    zona_id = fields.Many2one('induus.zona', string="Zonas")
    is_company = fields.Boolean(default=True)
    equipo_ids = fields.One2many('induus.equipo', 'partner_id')
    no_facturar_auto = fields.Boolean('No facturar automáticamente')
    validar_campos = fields.Boolean('Validar campos', default=True)
    seguimiento = fields.Boolean('Realizar seguimiento Proveedor')
    seguimiento_cliente = fields.Integer('Días del seguimiento oferta cliente', default=15, required=True)
    seguimiento_comercial = fields.Integer('Días del seguimiento comercial', default=7, required=True)
    purchase_order_line_pendientes_ids = fields.Many2many('purchase.order.line', string="Compras con plazo de entrega cumplido",
                                                 compute="_compute_purchase_order_line_pendientes")
    supplier_property_delivery_carrier_id = fields.Many2one('delivery.carrier', string="Método entrega")
    incoterm_id = fields.Many2one('account.incoterms', string="Incoterm")
    intrastat_country_id = fields.Many2one('res.country', string="País para el Intrasat")
    intrastat_transport_mode_id = fields.Many2one('account.intrastat.code', string="Modo de transporte Intrastat")
    country_code = fields.Char(related="country_id.code")
    sale_order_team_id = fields.Many2one('crm.team', string="Equipo de venta")
    agencia_genei_id = fields.Integer("ID agencia de Genei", default=2)
    no_mostrar_ref = fields.Boolean("No mostrar referencia")
    mostrar_ref_cliente = fields.Boolean("Mostrar ref. cliente")
    mostrar_ref_induus = fields.Boolean("Mostrar ref. Induus")
    intrastat_required_partner = fields.Boolean(related="property_account_position_id.intrastat_required_partner")

#     @api.multi
    @api.depends('country_id')
    def _compute_product_pricelist(self):
        company = self.env.context.get('force_company', False)
        res = self.env['product.pricelist']._get_partner_pricelist_multi(self.ids, company_id=company)
        for p in self:
            pricelist_id = res.get(p.id)
            p.property_product_pricelist = pricelist_id if pricelist_id else 108 # TARIFA PUBLICA

    @api.constrains('vat')
    def check_vat(self):
        return True

    @api.onchange('company_type')
    def _onchange_property_account_position_id(self):
        for r in self:
            if r.partner_share or r.is_company:
                r.property_account_position_id = False
            elif r.company_type == 'company' and not r.property_account_position_id:
                regimen_nacional = self.env.ref('l10n_es.fp_nacional', False)
                if regimen_nacional:
                    r.property_account_position_id = regimen_nacional.id

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for r in self:
            if r.parent_id:
                r.zona_id = r.parent_id.zona_id.id if r.parent_id.zona_id else None

    @api.onchange('is_company')
    def _onchange_supplier(self):
        for r in self:
            if r.is_company:
                r.seguimiento = True
            else:
                r.seguimiento = False

    def _compute_purchase_order_line_pendientes(self):
        for r in self:
            orders = self.env['purchase.order.line'].search([
                ('order_id.partner_id', '=', r.id),
                ('order_id.state', 'in', ['purchase']),
                ('product_id.type', '=', 'product'),
                ('date_planned', '<=', fields.Datetime.to_string((datetime.now() - relativedelta(days=2)).date()))
            ])

            order_ids = [ord.id for ord in orders.filtered(lambda o: o.qty_received < o.product_qty)]
            r.purchase_order_line_pendientes_ids = [(6, 0, order_ids)]

    @api.model
    def realizar_seguimiento(self):
        for r in self.filtered(lambda p: p.purchase_order_line_pendientes_ids and p.seguimiento):
            template = self.env.ref('induus.email_template_seguimiento_purchase_order')
            self.env['mail.template'].browse(template.id).send_mail(r.id)

            purchase_order_ids = [lpd.order_id.id for lpd in r.purchase_order_line_pendientes_ids]
            purchase_order = self.env['purchase.order'].search([
                ('id', 'in', purchase_order_ids),
                ('user_id', '!=', False),
            ])

            template = template.get_email_template(r.id)
            body_html = self.env['mail.template']._render_template(template.body_html, 'res.partner', r.id)
            if purchase_order:
                purchase_order.with_context(mail_create_nosubscribe=True).message_post(
                    body=body_html,
                    message_type='comment',
                    subtype='mail.mt_note'
                )

            for order in purchase_order:
                self.env['mail.activity'].create({
                    'activity_type_id': 2,
                    'summary': "Verificar reclamacion a proveedor",
                    'date_deadline': datetime.today(),
                    'user_id': order.user_id.id,
                    'res_model': 'purchase.order',
                    'res_model_id': self.env.ref('purchase.model_purchase_order').id,
                    'res_id': order.id,
                    'res_name': order.name,
                })

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if not self.env.context.get('partner_no_validation'):
            res.campos_obligatorios()
        if res.parent_id:
            values = {}
            if not vals.get('seguimiento_cliente'):
                values.update({'seguimiento_cliente': res.parent_id.seguimiento_cliente})

            if not vals.get('seguimiento_comercial'):
                values.update({'seguimiento_comercial': res.parent_id.seguimiento_comercial})

            if values:
                res.write(values)
                
        return res

#     @api.multi
    def write(self, vals):
        res = super(Partner, self).write(vals)
        if not self.env.context.get('partner_no_validation'):
            self.campos_obligatorios()
        
        if 'incoterm_id' in vals or 'intrastat_country_id' in vals or 'intrastat_transport_mode_id' in vals:
            self.update_intrastat_child_parent()
    
        return res

    def update_intrastat_child_parent(self):
        for r in self:
            if r.parent_id or not r.child_ids:
                continue
                
            r.child_ids.write({
                'incoterm_id': r.incoterm_id.id,
                'intrastat_country_id': r.intrastat_country_id.id,
                'intrastat_transport_mode_id': r.intrastat_transport_mode_id.id,
            })
                
    
    def actualizar_zona_child(self):
        for r in self:
            zona_id = r.zona_id.id if r.zona_id else None
            for c in r.child_ids:
                c.write({'zona_id': zona_id})

    def campos_obligatorios(self, con_validar_campos=True):
        for r in self:
            if r.type != 'contact' or (r.type == 'contact' and con_validar_campos and not r.validar_campos):
                continue

            def validar_campos_contacto(self, campos):
                for campo in campos:
                    if not eval("self.%s" % campo):
                        _logger.warning(campo) # No quitar el logger porque si no no funciona
                        raise ValidationError('El campo %s es obligatoria.' % self.fields_get([campo])[campo]['string'])

            if r.is_company:
                validar_campos_contacto(r, CAMPOS_OBLIGATORIOS_EMPRESA)
                if r.partner_share:
                    validar_campos_contacto(r, CAMPOS_OBLIGATORIOS_EMPRESA_CLIENTE)

                if r.is_company:
                    validar_campos_contacto(r, CAMPOS_OBLIGATORIOS_EMPRESA_PROVEEDOR)

            if r.partner_share:
                validar_campos_contacto(r, CAMPOS_OBLIGATORIOS_CLIENTE)

            if r.is_company:
                validar_campos_contacto(r, CAMPOS_OBLIGATORIOS_PROVEEDOR)

#     @api.multi
    def name_get(self):
        return super(Partner, self.with_context(no_display_commercial=True)).name_get()

#     @api.multi
    def fix_name_with_email(self):
        for r in self.filtered(lambda x: x.name.find('@') > -1):
            email_list = getaddresses([r.name.strip()])
            name = email_list[0][0]
            email = email_list[0][1]

            if name:
                r.write({
                    'name': name,
                    'email': email if not r.email else r.email
                })


class FiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    note2 = fields.Text('Notas 2', translate=True)
    fiscal_position_pay_model_ids = fields.One2many('induus.fiscal_position_payment_mode_rel', 'fiscal_position_id')

    def modo_pago(self, payment_model_id):
        self.ensure_one()
        if not payment_model_id:
            return None
        r = self.env['induus.fiscal_position_payment_mode_rel'].sudo().search([
            ('fiscal_position_id', '=', self.id),
            ('payment_mode_id', '=', payment_model_id),
        ], limit=1)
        return r and r.note or None


class FiscalPositionPaymentModeRel(models.Model):
    _name = 'induus.fiscal_position_payment_mode_rel'
    _description = "Relaciones posiciones fiscales con modo de pago"

    name = fields.Char('Nombre', compute="_compute_name", store=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string="Posición fiscal", required=True)
    payment_mode_id = fields.Many2one('account.payment.mode', string="Modo de pago", required=True)
    note = fields.Text('Nota', required=True, translate=True)

    _sql_constraints = [
        ('fiscal_position_pay_mode_uniq', 'unique (fiscal_position_id,payment_mode_id)', "La relación ya existe."),
    ]

    @api.depends('fiscal_position_id', 'payment_mode_id')
    def _compute_name(self):
        for r in self:
            r.name = "%s - %s" % (r.fiscal_position_id.name, r.payment_mode_id.name)
