odoo.define('init_web_tree_view.TreeModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel');

var TreeModel = AbstractModel.extend({
     init: function () {
            this._super.apply(this, arguments);
        },
    load: function (params) {
        this.modelName = params.modelName;
        this.fieldNames = params.fieldNames;
        this.res_id = params.res_id;
        this.data = {
            domain: params.domain,
            context: params.context,
        };
        return this._fetch_data_for_tree();
    },
    _fetch_data_for_tree: function () {
        var domain = [['parent_id', '=', false]];
        domain.push(...this.data.domain);
        var self = this;
            return self._rpc({
                model: self.modelName,
                method: 'search_read',
                context: self.data.context,
                fields: [],
                domain: domain,
            })
            .then(function (records) {
                self.data.data = records;
            });
    },
    reload: function () {
        return this._fetch_data_for_tree();
    },

});

return TreeModel;
});