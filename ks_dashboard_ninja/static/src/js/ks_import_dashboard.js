odoo.define('ks_dashboard_ninja.import_button', function(require) {

    "use strict";

    var core = require('web.core');
    var _t = core._t;
//    var Sidebar = require('web.Sidebar');
    var ListController = require('web.ListController');
    var framework = require('web.framework');
    var Dialog = require('web.Dialog');


    ListController.include({




       _getActionMenuItems: function (state) {
        if (!this.hasActionMenus || !this.selectedRecords.length) {
            return null;
        }
        const props = this._super(...arguments);
        const otherActionItems = [];
        if (this.modelName == "ks_dashboard_ninja.board"){
        if (this.isExportEnable) {
            otherActionItems.push({
                 description: _t("Export Dashboard"),
                callback: this.ks_dashboard_export.bind(this)
            });
        }
        if (this.archiveEnabled) {
            otherActionItems.push({
                description: _t("Archive"),
                callback: () => {
                    Dialog.confirm(this, _t("Are you sure that you want to archive all the selected records?"), {
                        confirm_callback: () => this._toggleArchiveState(true),
                    });
                }
            }, {
                description: _t("Unarchive"),
                callback: () => this._toggleArchiveState(false)
            });
        }
        if (this.activeActions.delete) {
            otherActionItems.push({
                description: _t("Delete"),
                callback: () => this._onDeleteSelectedRecords()
            });
        }}else{
            if (this.isExportEnable) {
            otherActionItems.push({
                description: _t("Export"),
                callback: () => this._onExportData()
            });
        }
        if (this.archiveEnabled) {
            otherActionItems.push({
                description: _t("Archive"),
                callback: () => {
                    Dialog.confirm(this, _t("Are you sure that you want to archive all the selected records?"), {
                        confirm_callback: () => this._toggleArchiveState(true),
                    });
                }
            }, {
                description: _t("Unarchive"),
                callback: () => this._toggleArchiveState(false)
            });
        }
        if (this.activeActions.delete) {
            otherActionItems.push({
                description: _t("Delete"),
                callback: () => this._onDeleteSelectedRecords()
            });
        }

        }
        return Object.assign(props, {
            items: Object.assign({}, this.toolbarActions, { other: otherActionItems }),
            context: state.getContext(),
            domain: state.getDomain(),
            isDomainSelected: this.isDomainSelected,
        });

    },

        ks_dashboard_export: function() {
            this.ks_on_dashboard_export(this.getSelectedIds());
        },

        ks_on_dashboard_export: function(ids) {
            var self = this;
            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_dashboard_export',
                args: [JSON.stringify(ids)],
            }).then(function(result) {
                var name = "dashboard_ninja";
                var data = {
                    "header": name,
                    "dashboard_data": result,
                }
                framework.blockUI();
                self.getSession().get_file({
                    url: '/ks_dashboard_ninja/export/dashboard_json',
                    data: {
                        data: JSON.stringify(data)
                    },
                    complete: framework.unblockUI,
                    error: (error) => this.call('crash_manager', 'rpc_error', error),
                });
            })
        },


    });
    core.action_registry.add('ks_dashboard_ninja.import_button', ListController);
    return ListController;
});