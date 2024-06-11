/** @odoo-module alias=web.window.title **/

import { WebClient } from "@web/webclient/webclient";
import {patch} from "@web/core/utils/patch";

patch(WebClient.prototype, {
    setup() {
        const title = document.title;
        super.setup();
        this.title.setParts({ zopenerp: title });
    }
});


//odoo.define('custom_module.custom_form_button_save', function (require) {
//    "use strict";
//
//    var FormController = require('web.FormController');
//
//    FormController.include({
//        // Override the _renderButtons method to replace the save button
//        _renderButtons: function () {
//            this._super.apply(this, arguments);
//            // Replace the save button with custom implementation
//            this.$buttons.find('.o_form_button_save').replaceWith('<button class="btn btn-primary o_form_button_save_custom">Custom Save</button>');
//        }
//    });
//
//    return FormController;
//});
