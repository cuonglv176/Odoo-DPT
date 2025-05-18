odoo.define('init_web_tree_view.TreeView', function (require) {
  "use strict";

  var core = require('web.core');
  var AbstractView = require('web.AbstractView');
  var BasicView = require('web.BasicView');

  var TreeModel = require('init_web_tree_view.TreeModel');
  var TreeRenderer = require('init_web_tree_view.TreeRenderer');
  var TreeController = require('init_web_tree_view.TreeController');

  var view_registry = require('web.view_registry');

  var _lt = core._lt;

  var InitTreeView = AbstractView.extend({
    display_name: _lt('INIT Tree View'),
    icon: 'fa-align-left',
    searchable: false,
    withSearchBar: false,
    withControlPanel: true,
    withSearchPanel: false,
    viewType: 'init_tree',
    searchMenuTypes: [],

    config: _.extend({}, BasicView.prototype.config, {
      Model: TreeModel,
      Renderer: TreeRenderer,
      Controller: TreeController,
    }),

    /**
     * @override
     * @param {Object} viewInfo
     * @param {Object} params
     */
    init: function (viewInfo, params) {
      this._super.apply(this, arguments);
      var self = this;
      this.init_tree = false;
      var attrs = this.arch.attrs;
      this.fields = viewInfo.fields;
      this.modelName = this.controllerParams.modelName;
      this.action = params.action;

      this.rendererParams.fields = this.fields;
      this.rendererParams.children_field = viewInfo.field_parent;
      this.rendererParams.model = this.modelName;
      this.rendererParams.arch = this.arch;
      this.rendererParams.context = params.context;
      this.rendererParams.action = params.action;
    },

  });

  view_registry.add('init_tree', InitTreeView);
  return InitTreeView;

});