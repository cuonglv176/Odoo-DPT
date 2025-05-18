odoo.define('init_web_tree_view.TreeController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;

var TreeController = AbstractController.extend({
    custom_events: {
    },
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.domain = params.domain || [];
        this.context = params.context;
    },
});

return TreeController;

});