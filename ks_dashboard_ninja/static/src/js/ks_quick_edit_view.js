/** @odoo-module **/


import Widget from "@web/legacy/js/core/widget";
import { _t } from "@web/core/l10n/translation";
//var data = require('web.data');
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
//var AbstractAction = require('web.AbstractAction');
import { session } from "@web/session";

var QuickEditView = Widget.extend({

    template: 'ksQuickEditViewOption',

    events: {
        'click .ks_quick_edit_action': 'ksOnQuickEditViewAction',
    },

    init: function(parent, options) {
        this._super.apply(this, arguments);
        this.ksDashboardController = parent;

        this.ksOriginalItemData = $.extend({}, options.item);
        this.item = options.item;
        this.item_name = options.item ? options.item.name:false;

    },


    willStart: function() {
        var self = this;
        return $.when(this._super()).then(function() {
            return self._ksCreateController();
        });
    },

    _ksCreateController: function() {
        var self = this;

        self.context = $.extend({}, session.user_context);
        self.context['form_view_ref'] = 'ks_dashboard_ninja.item_quick_edit_form_view';
        self.context['res_id'] = this.item.id;
        self.res_model = "ks_dashboard_ninja.item";
        self.dataset = new data.DataSet(this, this.res_model, self.context);
        var def = self.loadViews(this.dataset.model, self.context, [
            [false, 'list'],
            [false, 'form']
        ], {});
        return $.when(def).then(function(fieldsViews) {
            self.formView = new FormViewDialog(fieldsViews.form, {
                context: self.context,
                modelName: self.res_model,
                userContext: self.getSession().user_context,
                currentId: self.item.id,
                index: 0,
                mode: 'edit',
                footerToButtons: true,
                default_buttons: false,
                withControlPanel: false,
                ids: [self.item.id],
            });
            var def2 = self.formView.getController(self);
            return $.when(def2).then(function(controller) {
                self.controller = controller;
                self.controller._confirmChange = self._confirmChange.bind(self);
            });
        });
    },

    //This Function is replacing Controllers to intercept in between to fetch changed data and update our item view.
    _confirmChange: function(id, fields, e) {
        if (e.name === 'discard_changes' && e.target.reset) {
            // the target of the discard event is a field widget.  In that
            // case, we simply want to reset the specific field widget,
            // not the full view
            return e.target.reset(this.controller.model.get(e.target.dataPointID), e, true);
        }

        var state = this.controller.model.get(this.controller.handle);
        this.controller.renderer.confirmChange(state, id, fields, e);
        return this.ks_Update_item();
    },

    ks_Update_item: function() {
        var self = this;
        var ksChanges = this.controller.renderer.state.data;

        if (ksChanges['name']) this.item['name'] = ksChanges['name'];

        self.item['ks_font_color'] = ksChanges['ks_font_color'];
        self.item['ks_icon_select'] = ksChanges['ks_icon_select'];
//            self.item['ks_icon'] = ksChanges['ks_icon'];
        self.item['ks_background_color'] = ksChanges['ks_background_color'];
        self.item['ks_default_icon_color'] = ksChanges['ks_default_icon_color'];
        self.item['ks_layout'] = ksChanges['ks_layout'];
        self.item['ks_record_count'] = ksChanges['ks_record_count'];

        if (ksChanges['ks_list_view_data']) self.item['ks_list_view_data'] = ksChanges['ks_list_view_data'];

        if (ksChanges['ks_chart_data']) self.item['ks_chart_data'] = ksChanges['ks_chart_data'];

        if (ksChanges['ks_kpi_data']) self.item['ks_kpi_data'] = ksChanges['ks_kpi_data'];

        if (ksChanges['ks_list_view_type']) self.item['ks_list_view_type'] = ksChanges['ks_list_view_type'];

        if (ksChanges['ks_chart_item_color']) self.item['ks_chart_item_color'] = ksChanges['ks_chart_item_color'];

        self.ksUpdateItemView();

    },

    start: function() {
        var self = this;
        this._super.apply(this, arguments);

    },

    renderElement: function() {
        var self = this;
        self._super.apply(this, arguments);
        self.controller.appendTo(self.$el.find(".ks_item_field_info"));

        self.trigger('canBeRendered', {});
    },

    ksUpdateItemView: function() {
        var self = this;
        self.ksDashboardController.ksUpdateDashboardItem([self.item.id]);
        self.item_el = $.find('#' + self.item.id + '.ks_dashboarditem_id');

    },

    ksDiscardChanges: function() {
        var self = this;
        self.ksDashboardController.ksFetchUpdateItem(self.item.id);
        self.destroy();
    },


    ksOnQuickEditViewAction: function(e) {
        var self = this;
        self.need_reset = false;
        var options = {
            'need_item_reload': false
        }
        if (e.currentTarget.dataset['ksItemAction'] === 'saveItemInfo') {
            this.controller.saveRecord().then(function() {
                self.ksDiscardChanges();
            })
        } else if (e.currentTarget.dataset['ksItemAction'] === 'fullItemInfo') {
            this.trigger('openFullItemForm', {});
        } else {
            self.ksDiscardChanges();
        }
    },

    destroy: function(options) {
        this.trigger('canBeDestroyed', {});
        this.controller.destroy();
        this._super();
    },
});

return {
    QuickEditView: QuickEditView,
};