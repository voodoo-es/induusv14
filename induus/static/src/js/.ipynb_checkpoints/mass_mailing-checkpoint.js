odoo.define('induus.website_integration', function (require) {
"use strict";

var utils = require('web.utils');
var sAnimation = require('website.content.snippets.animation');

console.log("hola");

sAnimation.registry.subscribe_newsletter = sAnimation.Class.extend({
    selector: ".frm_subscribe",
    start: function () {
        console.log("inicio");
        var self = this;
        this.$target.find('.btn_suscribirse').on('click', function (event) {
            event.preventDefault();
            self._onClick();
        });
    },
    _onClick: function () {
        var self = this;
        var $email = this.$target.find(".subscribe_email:visible");
        var $politica_privacidad = this.$target.find("#acptpriv:visible");

        if ($email.length && !$email.val().match(/.+@.+/)) {
            this.$target.addClass('o_has_error').find('.form-control, .custom-select').addClass('is-invalid');
            return false;
        }

        this.$target.removeClass('o_has_error').find('.form-control, .custom-select').removeClass('is-invalid');

        if(!$politica_privacidad.is(':checked')){
            $("#lblacptpriv").css({'color': 'red'});
            return false;
        }
        $("#lblacptpriv").css({'color': 'white'});

        this._rpc({
            route: '/website_mass_mailing/subscribe',
            params: {
                'list_id': this.$target.data('list-id'),
                'email': $email.length ? $email.val() : false,
            },
        }).then(function (subscribe) {
            self.$target.find(".inpsubs").addClass('d-none');
            self.$target.find(".granews").removeClass('d-none');
        });
    },
});
});
