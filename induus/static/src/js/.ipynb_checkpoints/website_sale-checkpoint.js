odoo.define('induus.ProductConfiguratorMixin', function (require) {
'use strict';

var utils = require('web.utils');
var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
var sAnimations = require('website.content.snippets.animation');
var ajax = require('web.ajax');
var core = require('web.core');
var config = require('web.config');
var QWeb = core.qweb;
var xml_load = ajax.loadXML(
    '/website_sale_stock/static/src/xml/website_sale_stock_product_availability.xml',
    QWeb
);

var _t = core._t;

ProductConfiguratorMixin._onChangeCombinationStock = function (ev, $parent, combination) {
	var product_id = 0;
    // needed for list view of variants
    if ($parent.find('input.product_id:checked').length) {
        product_id = $parent.find('input.product_id:checked').val();
    } else {
        product_id = $parent.find('.product_id').val();
    }

    var isMainProduct = combination.product_id &&
        ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
        combination.product_id === parseInt(product_id);

    if (!this.isWebsite || !isMainProduct){
        return;
    }

    var qty = $parent.find('input[name="add_qty"]').val();

    $parent.find('#add_to_cart').removeClass('out_of_stock');
    if (combination.product_type === 'product' && _.contains(['always', 'threshold'], combination.inventory_availability)) {
        combination.virtual_available -= parseInt(combination.cart_qty);
        if (combination.virtual_available < 0) {
            combination.virtual_available = 0;
        }
        // Handle case when manually write in input
        if (qty > combination.virtual_available) {
            var $input_add_qty = $parent.find('input[name="add_qty"]');
            qty = combination.virtual_available || 1;
            $input_add_qty.val(qty);
        }
        if (qty > combination.virtual_available
            || combination.virtual_available < 1 || qty < 1) {
            $parent.find('#add_to_cart').addClass('disabled out_of_stock');
        }
    }
    
    $("#fecha_prevista").text((combination.fecha_entrega)? combination.fecha_entrega : '');
    
    xml_load.then(function () {
        $('.oe_website_sale')
            .find('.availability_message_' + combination.product_template)
            .remove();

        var $message = $(QWeb.render(
            'website_sale_stock.product_availability',
            combination
        ));
        $('div.availability_messages').html($message);
    });
};

return ProductConfiguratorMixin;
});
