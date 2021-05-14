odoo.define('induus.website_sale', function (require) {
    'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');

    $('#subscription_order').change(function(event){
        var anadir_suscripcion;
        if($(this).is(':checked')){
            anadir_suscripcion = true;
        }else{
            anadir_suscripcion = false;
        }
        var order_id = $(this).data('order_id');
        ajax.jsonRpc("/newsletter/order/" + order_id + "/add",
        "call",
        {
            "anadir_suscripcion": anadir_suscripcion
        })
        .then(function (data){
        });
    });
});
