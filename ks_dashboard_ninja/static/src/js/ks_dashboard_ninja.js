odoo.define('ks_dashboard_ninja.ks_dashboard', function(require) {
    "use strict";

    var core = require('web.core');
    const { patch } = require('web.utils');
    const { WebClient } = require("@web/webclient/webclient");
//    var export = require('ks_dashboard_ninja.import_button');
    var Dialog = require('web.Dialog');
    var viewRegistry = require('web.view_registry');
    var _t = core._t;
    var QWeb = core.qweb;
    var utils = require('web.utils');
    var config = require('web.config');
    var framework = require('web.framework');
    var time = require('web.time');
    var datepicker = require("web.datepicker");

    const session = require('web.session');
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var framework = require('web.framework');
    var field_utils = require('web.field_utils');
    var KsGlobalFunction = require('ks_dashboard_ninja.KsGlobalFunction');

    var KsQuickEditView = require('ks_dashboard_ninja.quick_edit_view');
    const { loadBundle } = require('@web/core/assets');


    var KsDashboardNinja = AbstractAction.extend({
        // To show or hide top control panel flag.
        hasControlPanel: false,

        dependencies: ['bus_service'],

        /**
         * @override
         */

        jsLibs: [
            '/ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js',
            '/ks_dashboard_ninja/static/lib/js/gridstack-h5.js',
            '/ks_dashboard_ninja/static/lib/js/chartjs-plugin-datalabels.js',
            '/ks_dashboard_ninja/static/lib/js/pdfmake.min.js',
            '/ks_dashboard_ninja/static/lib/js/vfs_fonts.js',
            'ks_dashboard_ninja/static/lib/js/Animated.js',
            'ks_dashboard_ninja/static/lib/js/worldLow.js',
            'ks_dashboard_ninja/static/lib/js/map.js',
            'ks_dashboard_ninja/static/lib/js/index.js',
            'ks_dashboard_ninja/static/lib/js/pdfmake.js',
            'ks_dashboard_ninja/static/lib/js/percent.js',
            'ks_dashboard_ninja/static/lib/js/pdf.min.js',
            'ks_dashboard_ninja/static/lib/js/print.min.js',
        ],
        cssLibs: ['/ks_dashboard_ninja/static/lib/css/Chart.css',
            '/ks_dashboard_ninja/static/lib/css/Chart.min.css'
        ],

        init: function(parent, state, params) {
//            css_grid = $('.o_rtl').length>0 ?
            this._super.apply(this, arguments);
            this.reload_menu_option = {
                reload: state.context.ks_reload_menu,
                menu_id: state.context.ks_menu_id
            };
            this.ks_mode = 'active';
            this.action_manager = parent;
            this.controllerID = params.controllerID;
            this.name = "ks_dashboard";
            this.ksIsDashboardManager = false;
            this.ksDashboardEditMode = false;
            this.ksNewDashboardName = false;
            this.file_type_magic_word = {
                '/': 'jpg',
                'R': 'gif',
                'i': 'png',
                'P': 'svg+xml',
            };
            this.ksAllowItemClick = true;

            //Dn Filters Iitialization
            var l10n = _t.database.parameters;
            this.form_template = 'ks_dashboard_ninja_template_view';
            this.date_format = time.strftime_to_moment_format(_t.database.parameters.date_format)
            this.date_format = this.date_format.replace(/\bYY\b/g, "YYYY");
            this.datetime_format = time.strftime_to_moment_format((_t.database.parameters.date_format + ' ' + l10n.time_format))
            //            this.is_dateFilter_rendered = false;
            this.ks_date_filter_data;

            // Adding date filter selection options in dictionary format : {'id':{'days':1,'text':"Text to show"}}
            this.ks_date_filter_selections = {
                'l_none': _t('Date Filter'),
                'l_day': _t('Today'),
                't_week': _t('This Week'),
                'td_week': _t('Week To Date'),
                't_month': _t('This Month'),
                'td_month': _t('Month to Date'),
                't_quarter': _t('This Quarter'),
                'td_quarter': _t('Quarter to Date'),
                't_year': _t('This Year'),
                'td_year': _t('Year to Date'),
                'n_day': _t('Next Day'),
                'n_week': _t('Next Week'),
                'n_month': _t('Next Month'),
                'n_quarter': _t('Next Quarter'),
                'n_year': _t('Next Year'),
                'ls_day': _t('Last Day'),
                'ls_week': _t('Last Week'),
                'ls_month': _t('Last Month'),
                'ls_quarter': _t('Last Quarter'),
                'ls_year': _t('Last Year'),
                'l_week': _t('Last 7 days'),
                'l_month': _t('Last 30 days'),
                'l_quarter': _t('Last 90 days'),
                'l_year': _t('Last 365 days'),
                'ls_past_until_now': _t('Past Till Now'),
                'ls_pastwithout_now': _t('Past Excluding Today'),
                'n_future_starting_now': _t('Future Starting Now'),
                'n_futurestarting_tomorrow': _t('Future Starting Tomorrow'),
                'l_custom': _t('Custom Filter'),
            };
            // To make sure date filter show date in specific order.
            this.ks_date_filter_selection_order = ['l_day', 't_week', 't_month', 't_quarter','t_year',
                'td_week','td_month','td_quarter', 'td_year','n_day','n_week', 'n_month', 'n_quarter', 'n_year',
                'ls_day','ls_week', 'ls_month', 'ls_quarter', 'ls_year', 'l_week', 'l_month', 'l_quarter', 'l_year',
                'ls_past_until_now', 'ls_pastwithout_now','n_future_starting_now', 'n_futurestarting_tomorrow',
                 'l_custom'
            ];

            this.ks_dashboard_id = state.params.ks_dashboard_id;

            this.gridstack_options = {
                staticGrid:true,
                float: false,
                cellHeight: 80,
                styleInHead : true,
//                disableOneColumnMode: true,

            };
            if (config.device.isMobileDevice) {
                this.gridstack_options.disableOneColumnMode = false
            }
            this.gridstackConfig = {};
            this.grid = false;
            this.chartMeasure = {};
            this.chart_container = {};
            this.list_container = {};


            this.ksChartColorOptions = ['default', 'cool', 'warm', 'neon'];
            this.ksUpdateDashboardItem = this.ksUpdateDashboardItem.bind(this);


            this.ksDateFilterSelection = false;
            this.ksDateFilterStartDate = false;
            this.ksDateFilterEndDate = false;
            this.ksUpdateDashboard = {};
            $("head").append('<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">');
            if(state.context.ks_reload_menu){
                this.trigger_up('reload_menu_data', { keep_open: true, scroll_to_bottom: true});
            }
            var context = {
                ksDateFilterSelection: self.ksDateFilterSelection,
                ksDateFilterStartDate: self.ksDateFilterStartDate,
                ksDateFilterEndDate: self.ksDateFilterEndDate,
            }
            this.state = {}
            this.state['user_context']=context
        },

        getContext: function() {
            var self = this;
            var context = {
                ksDateFilterSelection: self.ksDateFilterSelection,
                ksDateFilterStartDate: self.ksDateFilterStartDate,
                ksDateFilterEndDate: self.ksDateFilterEndDate,
            }
            if(self.state['user_context']['ksDateFilterSelection'] !== undefined && self.ksDateFilterSelection !== 'l_none'){
                context = self.state['user_context']
            }
            return Object.assign(context, session.user_context);
        },

        on_attach_callback: function() {
            var self = this;
            $.when(self.ks_fetch_items_data()).then(function(result){
                self.ksRenderDashboard();
                self.ks_set_update_interval();
                if (self.ks_dashboard_data.ks_item_data) {
                    self._ksSaveCurrentLayout();
                    session.user_context['gridstack_config'] = self.ks_get_current_gridstack_config();
                }
            });
        },

        ks_set_update_interval: function() {
            var self = this;
            if (self.ks_dashboard_data.ks_item_data) {

                Object.keys(self.ks_dashboard_data.ks_item_data).forEach(function(item_id) {
                    var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                    var updateValue = self.ks_dashboard_data.ks_set_interval;
                    if (updateValue) {
                        if (!(item_id in self.ksUpdateDashboard)) {
                            if (['ks_tile', 'ks_list_view', 'ks_kpi', 'ks_to_do'].indexOf(item_data['ks_dashboard_item_type']) >= 0) {
                                var ksItemUpdateInterval = setInterval(function() {
                                    self.ksFetchUpdateItem(item_id)
                                }, updateValue);
                            } else {
                                var ksItemUpdateInterval = setInterval(function() {
                                    self.ksFetchChartItem(item_id)
                                }, updateValue);
                            }
                            self.ksUpdateDashboard[item_id] = ksItemUpdateInterval;
                        }
                    }
                });
            }
        },


        on_detach_callback: function() {
            var self = this;
            self.ks_remove_update_interval();
            if (self.ksDashboardEditMode) self._ksSaveCurrentLayout();

            self.ksDateFilterSelection = false;
            self.ksDateFilterStartDate = false;
            self.ksDateFilterEndDate = false;
//            self.ks_fetch_data();
        },

        ks_remove_update_interval: function() {
            var self = this;
            if (self.ksUpdateDashboard) {
                Object.values(self.ksUpdateDashboard).forEach(function(itemInterval) {
                    clearInterval(itemInterval);
                });
                self.ksUpdateDashboard = {};
            }
        },


        events: {
            'click #ks_add_item_selection > li': 'onAddItemTypeClick',
            'click .ks_dashboard_add_layout': '_onKsAddLayoutClick',
            'click .ks_dashboard_edit_layout': '_onKsEditLayoutClick',
            'click .ks_dashboard_select_item': 'onKsSelectItemClick',
            'click .ks_dashboard_save_layout': '_onKsSaveLayoutClick',
            'click .ks_dashboard_create_new_layout': '_onKsCreateLayoutClick',
            'click .ks_dashboard_cancel_layout': '_onKsCancelLayoutClick',
            'click .ks_item_click': '_onKsItemClick',
            'click .ks_load_previous': 'ksLoadPreviousRecords',
            'click .ks_load_next': 'ksLoadMoreRecords',
            //            'click .ks_dashboard_item_action': '_onKsItemActionClick',
            'click .ks_dashboard_item_customize': '_onKsItemCustomizeClick',
            'click .ks_dashboard_item_delete': '_onKsDeleteItemClick',
            'change .ks_dashboard_header_name': '_onKsInputChange',
            'click .ks_duplicate_item': 'onKsDuplicateItemClick',
            'click .ks_move_item': 'onKsMoveItemClick',
            'change .ks_input_import_item_button': 'ksImportItem',
            'click .ks_item_description':'ksstopclick',
            'click .ks_dashboard_menu_container': function(e) {
                e.stopPropagation();
            },
            'click .ks_qe_dropdown_menu': function(e) {
                e.stopPropagation();
            },
            'click .ks_chart_json_export': 'ksItemExportJson',
            'click .ks_dashboard_item_action': 'ksStopClickPropagation',
            'show.bs.dropdown .ks_dropdown_container': 'onKsDashboardMenuContainerShow',
            'hide.bs.dropdown .ks_dashboard_item_button_container': 'onKsDashboardMenuContainerHide',

            //  Dn Filters Events
            'click .apply-dashboard-date-filter': '_onKsApplyDateFilter',
            'click .clear-dashboard-date-filter': '_onKsClearDateValues',
            'change #ks_start_date_picker': '_ksShowApplyClearDateButton',
            'change #ks_end_date_picker': '_ksShowApplyClearDateButton',
            'click .ks_date_filters_menu': '_ksOnDateFilterMenuSelect',
            'click #ks_item_info': 'ksOnListItemInfoClick',
            'click .ks_chart_color_options': 'ksRenderChartColorOptions',
            'click #ks_chart_canvas_id': 'onChartCanvasClick',
            'click .ks_list_canvas_click': 'onChartCanvasClick',
            'click .ks_dashboard_item_chart_info': 'onChartMoreInfoClick',
            'click .ks_chart_xls_csv_export': 'ksChartExportXlsCsv',
            'click .ks_chart_pdf_export': 'ksChartExportPdf',

            'click .ks_dashboard_quick_edit_action_popup': 'ksOnQuickEditView',
            'click .ks_edit_map_form': 'ksOnQuickEditView',
            'click .ks_dashboard_item_drill_up': 'ksOnDrillUp',

            'click .ks_dashboard_layout_event': '_ksOnDnLayoutMenuSelect',
            'click .ks_dashboard_set_current_layout': '_ksSetCurrentLayoutClick',
            'click .ks_dashboard_cancel_current_layout': '_ksSetDiscardCurrentLayoutClick',
            'click .ks_add_dashboard_item_on_empty' : 'ks_add_dashboard_item_on_empty',
            'click #dashboard_settings': 'ksOnDashboardSettingClick',
            'click #dashboard_delete': 'ksOnDashboardDeleteClick',
            'click #dashboard_create': 'ksOnDashboardCreateClick',
            'click #dashboard_export': 'ksOnDashboardExportClick',
            'click #dashboard_import': 'ksOnDashboardImportClick',
            'click #dashboard_duplicate': 'ksOnDashboardDuplicateClick',
            'click #ks_ai_item_dash' : 'createaidash',
            'click #create_ai_dashboard' :'createaidashboard'
        },



        ksOnDashboardDuplicateClick: function(ev){
         ev.preventDefault();
            var self= this;
            var dashboard_id = this.ks_dashboard_id;
            this._rpc({
                model: 'ks.dashboard.duplicate.wizard',
                method: "DuplicateDashBoard",
                args: [self.ks_dashboard_id],
                }).then((result)=>{
                    self.do_action(result)

                });

        },

        ksOnDashboardImportClick: function(ev){
         ev.preventDefault();
            var self = this;
            var dashboard_id = this.ks_dashboard_id;
            this._rpc({
                    model: 'ks_dashboard_ninja.board',
                    method: 'ks_open_import',
                    args: [dashboard_id],
                    kwargs: {
                        dashboard_id: dashboard_id
                    }
                    }).then((result)=>{
                    self.do_action(result)
                    });
        },

        ksOnDashboardExportClick: function(ev){
         ev.preventDefault();
           var self= this;
           var dashboard_id = JSON.stringify(this.ks_dashboard_id);
                this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: "ks_dashboard_export",
                args: [dashboard_id],
                kwargs: {
                        dashboard_id: dashboard_id
                    }
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
            });
        },

        ksOnDashboardSettingClick: function(ev){
//         ev.preventDefault();
//            var self = this;

//            this._rpc({
//                    model: 'ks_dashboard_ninja.board',
//                    method: 'ks_open_setting',
//                    args: [dashboard_id],
//                    kwargs: {
//                        dashboard_id: dashboard_id
//                    }
//                    }).then((result)=>{
//                    self.do_action(result)
//                    });
         var self= this;
         var dashboard_id = this.ks_dashboard_id;
         var action = {
                name: _t('ks_open_setting'),
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.board',
                res_id: dashboard_id,
                domain: [],
                context: {'create':false
                },
                views: [
                    [false, 'form']
                ],
                view_mode: 'form',
                target: 'new',
           }
           self.do_action(action)

        },

        ksOnDashboardDeleteClick: function(ev){
         ev.preventDefault();
           var dashboard_id = this.ks_dashboard_id;
           var self= this;
                this._rpc({
                model: 'ks.dashboard.delete.wizard',
                method: "DeleteDashBoard",
                args: [self.ks_dashboard_id],
            }).then((result)=>{
                    self.do_action(result);
              });

        },

        ksOnDashboardCreateClick: function(ev){
           var self= this;
//                this._rpc({
//                model: 'ks.dashboard.wizard',
//                method: "CreateDashBoard",
//                args: [''],
//            }).then((result)=>{
//                self.do_action(result);
//              });
           var action = {
                name: _t('Create Dashboard'),
                type: 'ir.actions.act_window',
                res_model: 'ks.dashboard.wizard',
                domain: [],
                context: {
                },
                views: [
                    [false, 'form']
                ],
                view_mode: 'form',
                target: 'new',
           }
           self.do_action(action)

        },


        _ksOnDnLayoutMenuSelect: function(ev){
            var selected_layout_id = $(ev.currentTarget).data('ks_layout_id');
            this.ksOnLayoutSelection(selected_layout_id);

        },

        ksOnLayoutSelection: function(layout_id){
            var self = this;
            var selected_layout_name = this.ks_dashboard_data.ks_child_boards[layout_id][0];
            var selected_layout_grid_config = this.ks_dashboard_data.ks_child_boards[layout_id][1];
            this.gridstackConfig = JSON.parse(selected_layout_grid_config);
            _(this.gridstackConfig).each((x,y)=>{
                self.grid.update(self.$el.find(".grid-stack-item[gs-id=" + y + "]")[0],{ x:x['x'], y:x['y'], w:x['w'], h:x['h'],autoPosition:false});
            });


//            this.ks_dashboard_data.ks_selected_board_id = layout_id;
            this.$el.find("#ks_dashboard_layout_dropdown_container .ks_layout_selected").removeClass("ks_layout_selected");
            this.$el.find("li.ks_dashboard_layout_event[data-ks_layout_id='"+ layout_id + "']").addClass('ks_layout_selected');
            this.$el.find("#ks_dn_layout_button span:first-child").text(selected_layout_name);
            this.$el.find(".ks_dashboard_top_menu .ks_dashboard_top_settings").addClass("ks_hide");
            this.$el.find(".ks_dashboard_top_menu .ks_am_content_element").addClass("ks_hide");
            this.$el.find(".ks_dashboard_layout_edit_mode_settings").removeClass("ks_hide");
        },

        _ksSetCurrentLayoutClick: function(){
            var self = this;
            this.ks_dashboard_data.ks_selected_board_id = this.$el.find("#ks_dashboard_layout_dropdown_container .ks_layout_selected").data('ks_layout_id');
            this.$el.find(".ks_dashboard_top_menu .ks_dashboard_top_settings").removeClass("ks_hide");
            this.$el.find(".ks_dashboard_top_menu .ks_am_content_element").removeClass("ks_hide");
            this.$el.find(".ks_dashboard_layout_edit_mode_settings").addClass("ks_hide");
//            $('#ks_dashboard_title_input').val(this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][0]);
            this.ks_dashboard_data.name = this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][0];

            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'update_child_board',
                args: ['update', self.ks_dashboard_id, {
                    "ks_selected_board_id": this.ks_dashboard_data.ks_selected_board_id,
                }],
            }).then(function(){
                window.location.reload();
            });
        },

        _ksSetDiscardCurrentLayoutClick: function(){
            this.ksOnLayoutSelection(this.ks_dashboard_data.ks_selected_board_id);
            this.$el.find(".ks_dashboard_top_menu .ks_dashboard_top_settings").removeClass("ks_hide");
            this.$el.find(".ks_dashboard_top_menu .ks_am_content_element").removeClass("ks_hide");
            this.$el.find(".ks_dashboard_layout_edit_mode_settings").addClass("ks_hide");

        },


        ksOnQuickEditView: function(e) {
            var self = this;
            var item_id = e.currentTarget.dataset.itemId;
            var item_data = this.ks_dashboard_data.ks_item_data[item_id];
            var item_el = $.find('[gs-id=' + item_id + ']');
            var $quickEditButton = $(QWeb.render('ksQuickEditButtonContainer', {
                grid: $.extend({}, item_el[0].gridstackNode)
            }));
            $(item_el).before($quickEditButton);

            var ksQuickEditViewWidget = new KsQuickEditView.QuickEditView(this, {
                item: item_data,
            });

            ksQuickEditViewWidget.appendTo($quickEditButton.find('.dropdown-menu'));

            ksQuickEditViewWidget.on("canBeDestroyed", this, function(result) {
                if (ksQuickEditViewWidget) {
                    ksQuickEditViewWidget = false;
                    $quickEditButton.find('.ks_dashboard_item_action').click();
                }
            });

            ksQuickEditViewWidget.on("canBeRendered", this, function(result) {
                $quickEditButton.find('.ks_dashboard_item_action').click();
            });

            ksQuickEditViewWidget.on("openFullItemForm", this, function(result) {
                ksQuickEditViewWidget.destroy();
                $quickEditButton.find('.ks_dashboard_item_action').click();
                self.ks_open_item_form_page(parseInt(item_id));
            });


            $quickEditButton.on("hide.bs.dropdown", function(ev) {
                try {
                    if (ev.hasOwnProperty("clickEvent") && document.contains(ev.clickEvent.target) && !$(event.path[2]).hasClass('ui-menu ui-widget ui-widget-content ui-autocomplete dropdown-menu ui-front')) {
                        if (ksQuickEditViewWidget) {
                            ksQuickEditViewWidget.ksDiscardChanges();
                            ksQuickEditViewWidget = false;
                            self.ks_set_update_interval();
                            $quickEditButton.remove();
                        } else {
                            self.ks_set_update_interval();
                            $quickEditButton.remove();
                        }
                    } else if (!ev.hasOwnProperty("clickEvent")) {
                        self.ks_set_update_interval();
                        $quickEditButton.remove();
                    } else {
                        return false;
                    }
                }
                catch(e) {
                    return false;
                }
            });

            $quickEditButton.on("show.bs.dropdown", function() {
                self.ks_remove_update_interval();
            });

            e.stopPropagation();
        },

        willStart: function() {
            var self = this;
            var def;
            if (this.reload_menu_option.reload && this.reload_menu_option.menu_id) {
                def = this.getParent().actionService.ksDnReloadMenu(this.reload_menu_option.menu_id);
            }
            return $.when(def, loadBundle(this), this._super()).then(function() {
                return self.ks_fetch_data();
            });
        },

        start: function() {
            var self = this;
            self.ks_set_default_chart_view();
            return this._super()
        },

        ks_set_default_chart_view: function() {
            Chart.plugins.unregister(ChartDataLabels);
            var backgroundColor = 'white';
            Chart.plugins.register({
                beforeDraw: function(c) {
                    var ctx = c.chart.ctx;
                    ctx.fillStyle = backgroundColor;
                    ctx.fillRect(0, 0, c.chart.width, c.chart.height);
                }
            });
            Chart.plugins.register({
                afterDraw: function(chart) {
                    if (chart.data.labels.length === 0) {
                        // No data is present
                        var ctx = chart.chart.ctx;
                        var width = chart.chart.width;
                        var height = chart.chart.height
                        chart.clear();

                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.font = "3rem 'Lucida Grande'";
                        ctx.fillText('No data available', width / 2, height / 2);
                        ctx.restore();
                    }
                }

            });

            Chart.Legend.prototype.afterFit = function() {
                var chart_type = this.chart.config.type;
                if (chart_type === "pie" || chart_type === "doughnut") {
                    this.height = this.height;
                } else {
                    this.height = this.height + 20;
                };
            };
        },

        ksFetchUpdateItem: function(item_id) {
            var self = this;
            return self._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_item',
                args: [
                    [parseInt(item_id)], self.ks_dashboard_id, self.ksGetParamsForItemFetch(parseInt(item_id))
                ],
                context: self.getContext(),
            }).then(function(new_item_data) {
                this.ks_dashboard_data.ks_item_data[item_id] = new_item_data[item_id];
                this.ksUpdateDashboardItem([item_id]);
            }.bind(this));
        },

        ksRenderChartColorOptions: function(e) {
            var self = this;
            if (!$(e.currentTarget).parent().hasClass('ks_date_filter_selected')) {
                //            FIXME : Correct this later.
                var $parent = $(e.currentTarget).parent().parent();
                $parent.find('.ks_date_filter_selected').removeClass('ks_date_filter_selected')
                $(e.currentTarget).parent().addClass('ks_date_filter_selected')
                var item_data = self.ks_dashboard_data.ks_item_data[$parent.data().itemId];
                var chart_data = JSON.parse(item_data.ks_chart_data);
                if(item_data.ks_dashboard_item_type != "ks_funnel_chart" && item_data.ks_dashboard_item_type != "ks_bullet_chart" && item_data.ks_dashboard_item_type != "ks_flower_view" && item_data.ks_dashboard_item_type != "ks_radialBar_chart"){
                    this.ksChartColors(e.currentTarget.dataset.chartColor, this.chart_container[$parent.data().itemId], $parent.data().chartType, $parent.data().chartFamily, item_data.ks_bar_chart_stacked, item_data.ks_semi_circle_chart, item_data.ks_show_data_value, chart_data, item_data)
                    this._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'write',
                        args: [$parent.data().itemId, {
                            "ks_chart_item_color": e.currentTarget.dataset.chartColor
                    }],
                    }).then(function() {
                    self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_chart_item_color'] = e.currentTarget.dataset.chartColor;
                });
                }else if (item_data.ks_dashboard_item_type == "ks_funnel_chart" ||item_data.ks_dashboard_item_type == "ks_bullet_chart"){
                    this._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'write',
                        args: [$parent.data().itemId, {
                            "ks_funnel_item_color": e.currentTarget.dataset.chartColor
                    }],
                    }).then(function() {
                    self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_funnel_item_color'] = e.currentTarget.dataset.chartColor;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    if(item_data.ks_dashboard_item_type == "ks_funnel_chart"){
                        self.ksrenderfunnelchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                    }else if(item_data.ks_dashboard_item_type == "ks_bullet_chart"){
                        self.ksrenderbulletchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                    }
                    });
                }else if (item_data.ks_dashboard_item_type == "ks_flower_view"){
                    this._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'write',
                        args: [$parent.data().itemId, {
                            "ks_flower_item_color": e.currentTarget.dataset.chartColor
                        }],
                    }).then(function() {
                        self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_flower_item_color'] = e.currentTarget.dataset.chartColor;
                        self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                        self.ksrenderflowerchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                    });
                }else if (item_data.ks_dashboard_item_type == "ks_radialBar_chart"){
                    this._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'write',
                        args: [$parent.data().itemId, {
                            "ks_radial_item_color": e.currentTarget.dataset.chartColor
                        }],
                    }).then(function() {
                        self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_radial_item_color'] = e.currentTarget.dataset.chartColor;
                        self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                        self.ksrenderradialchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                    });
                }
            }
        },

        //To fetch dashboard data.
        ks_fetch_data: function() {
            var self = this;
            return this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_dashboard_data',
                args: [self.ks_dashboard_id],
                context: self.getContext(),
            }).then(function(result) {
//                result = self.normalize_dn_data(result);
                self.ks_dashboard_data = result;
                if(self.state['domain_data'] != undefined){
                    self.ks_dashboard_data.ks_dashboard_domain_data=self.state['domain_data']
                    Object.values(self.ks_dashboard_data.ks_dashboard_pre_domain_filter).map((x)=>{
                        if(self.state['domain_data'][x['model']] != undefined){
                            if(self.state['domain_data'][x['model']]['ks_domain_index_data'][0]['label'].indexOf(x['name']) ==-1){
                                self.ks_dashboard_data.ks_dashboard_pre_domain_filter[x['id']].active = false;
                            }
                        }
                        else{
                            self.ks_dashboard_data.ks_dashboard_pre_domain_filter[x['id']].active = false;
                        }
                    })
                }
            });
        },

        normalize_dn_data: function(result){
            _(result.ks_child_boards).each((x,y)=>{if (typeof(y)==='number'){
                result[y.toString()] = result[y];
                delete result[y];
            }})
            return result;
        },

        ks_fetch_items_data: function(){
            var self = this;
            var items_promises = []
            self.ks_dashboard_data.ks_dashboard_items_ids.forEach(function(item_id){
                items_promises.push(self._rpc({
                    model: "ks_dashboard_ninja.board",
                    method: "ks_fetch_item",
                    context: self.getContext(),
                    args : [[item_id], self.ks_dashboard_id, self.ksGetParamsForItemFetch(item_id)]
                }).then(function(result){
                    self.ks_dashboard_data.ks_item_data[item_id] = result[item_id];
                }));
            });

            return Promise.all(items_promises)
        },

        ksGetParamsForItemFetch: function(){
            return {};
        },

        on_reverse_breadcrumb: function(state) {
            var self = this;
            self.trigger_up('push_state', {
                controllerID: this.controllerID,
                state: state || {},
            });
            return $.when(self.ks_fetch_data());
        },

        ksstopclick:function(e) {
        this.ksAllowItemClick = false;;

        },

        ksStopClickPropagation: function(e) {
            this.ksAllowItemClick = false;
        },

        onKsDashboardMenuContainerShow: function(e) {
            $(e.currentTarget).addClass('ks_dashboard_item_menu_show');
            var item_id = e.currentTarget.dataset.item_id;
            if (this.ksUpdateDashboard[item_id]){
                clearInterval(this.ksUpdateDashboard[item_id]);
                delete this.ksUpdateDashboard[item_id]
            }

            //            Dynamic Bootstrap menu populate Image Report
            if ($(e.target.parentElement).hasClass('ks_dashboard_more_action')) {
                var chart_id = e.target.parentElement.dataset.itemId;
                var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
                var base64_image
                if(this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_bullet_chart" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_funnel_chart" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_flower_view" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_radialBar_chart" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_map_view"){
                    base64_image = (this.chart_container[chart_id].root.dom).querySelector("canvas").toDataURL("image/png")
                }else{
                    base64_image = this.chart_container[chart_id].toBase64Image();
                }
                $(e.target.parentElement).find('.dropdown-menu').empty();
                $(e.target.parentElement).find('.dropdown-menu').append($(QWeb.render('ksMoreChartOptions', {
                    href: base64_image,
                    download_fileName: name,
                    chart_id: chart_id
                })))
                }
            },


        onKsDashboardMenuContainerHide: function(e) {
            var self = this;
            $(e.currentTarget).removeClass('ks_dashboard_item_menu_show');
            var item_id = e.currentTarget.dataset.item_id;
            var updateValue = self.ks_dashboard_data.ks_set_interval;
            if (updateValue) {
                var updateinterval = setInterval(function() {
                    self.ksFetchUpdateItem(item_id)
                }, updateValue);
                self.ksUpdateDashboard[item_id] = updateinterval;
            }
            if (this.ks_dashboard_data.ks_item_data[item_id]['isDrill'] == true) {
                clearInterval(this.ksUpdateDashboard[item_id]);
            }
        },

        ks_get_dark_color: function(color, opacity, percent) {
            var num = parseInt(color.slice(1), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
        },


        //    This is to convert color #value into RGB format to add opacity value.
        _ks_get_rgba_format: function(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        },

        ksRenderDashboard: function() {
            var self = this;
            self.$el.empty();
            self.$el.addClass('ks_dashboard_ninja d-flex flex-column');
            var dash_name = $('ul[id="ks_dashboard_layout_dropdown_container"] li[class="ks_dashboard_layout_event ks_layout_selected"] span').text()
            if (self.ks_dashboard_data.ks_child_boards) self.ks_dashboard_data.name = this.ks_dashboard_data.ks_child_boards[self.ks_dashboard_data.ks_selected_board_id][0];
            var $ks_header = $(QWeb.render('ksDashboardNinjaHeader', {
                ks_dashboard_name: self.ks_dashboard_data.name,
                ks_multi_layout: self.ks_dashboard_data.multi_layouts,
                ks_dash_name: self.ks_dashboard_data.name,
                ks_dashboard_manager: self.ks_dashboard_data.ks_dashboard_manager,
                date_selection_data: self.ks_date_filter_selections,
                date_selection_order: self.ks_date_filter_selection_order,
                ks_show_create_layout_option: (Object.keys(self.ks_dashboard_data.ks_item_data).length > 0) && self.ks_dashboard_data.ks_dashboard_manager,
                ks_show_layout: self.ks_dashboard_data.ks_dashboard_manager && self.ks_dashboard_data.ks_child_boards && true,
                ks_selected_board_id: self.ks_dashboard_data.ks_selected_board_id,
                ks_child_boards: self.ks_dashboard_data.ks_child_boards,
                ks_dashboard_data: self.ks_dashboard_data,
                ks_dn_pre_defined_filters: _(self.ks_dashboard_data.ks_dashboard_pre_domain_filter).values().sort(function(a, b){return a.sequence - b.sequence}),
            }));

            if (!config.device.isMobile) {
                $ks_header.addClass("ks_dashboard_header_sticky")
            }

            self.$el.append($ks_header);
            if (Object.keys(self.ks_dashboard_data.ks_item_data).length===0){
                self.$el.find('.ks_dashboard_link').addClass("d-none");
                self.$el.find('.ks_dashboard_edit_layout').addClass("d-none");
            }
            self.ksRenderDashboardMainContent();
            if (Object.keys(self.ks_dashboard_data.ks_item_data).length === 0) {
                self._ksRenderNoItemView();
            }

        },

        ksRenderDashboardMainContent: function() {
            var self = this;
            if (config.device.isMobile && $('#ks_dn_layout_button :first-child').length > 0) {
                $('.ks_am_element').append($('#ks_dn_layout_button :first-child')[0].innerText);
                this.$el.find("#ks_dn_layout_button").addClass("ks_hide");
            }
            if (self.ks_dashboard_data.ks_item_data) {
                self._renderDateFilterDatePicker();

                self.$el.find('.ks_dashboard_link').removeClass("ks_hide");

                $('.ks_dashboard_items_list').remove();
                var $dashboard_body_container = $(QWeb.render('ks_main_body_container'))
                var $gridstackContainer = $dashboard_body_container.find(".grid-stack");
                $dashboard_body_container.appendTo(self.$el)
                self.grid = GridStack.init(self.gridstack_options,$gridstackContainer[0]);
                var items = self.ksSortItems(self.ks_dashboard_data.ks_item_data);

                self.ksRenderDashboardItems(items);

                // In gridstack version 0.3 we have to make static after adding element in dom
                self.grid.setStatic(true);

            } else if (!self.ks_dashboard_data.ks_item_data) {
                self.$el.find('.ks_dashboard_link').addClass("ks_hide");
                self._ksRenderNoItemView();
            }
        },

        // This function is for maintaining the order of items in mobile view
        ksSortItems: function(ks_item_data) {
            var items = []
            var self = this;
            var item_data = Object.assign({}, ks_item_data);
            if (self.ks_dashboard_data.ks_gridstack_config) {
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
                var a = Object.values(self.gridstackConfig);
                var b = Object.keys(self.gridstackConfig);
                for (var i = 0; i < a.length; i++) {
                    a[i]['id'] = b[i];
                }
                a.sort(function(a, b) {
                    return (35 * a.y + a.x) - (35 * b.y + b.x);
                });
                for (var i = 0; i < a.length; i++) {
                    if (item_data[a[i]['id']]) {
                        items.push(item_data[a[i]['id']]);
                        delete item_data[a[i]['id']];
                    }
                }
            }

            return items.concat(Object.values(item_data));
        },

        ksRenderDashboardItems: function(items) {
            var self = this;
            self.$el.find('.print-dashboard-btn').addClass("ks_pro_print_hide");
            if (self.ks_dashboard_data.ks_gridstack_config) {
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
            }
            var item_view;
            var ks_container_class = 'grid-stack-item',
                ks_inner_container_class = 'grid-stack-item-content';
                for (var i = 0; i < items.length; i++) {
                if (self.grid) {

                    if (items[i].ks_dashboard_item_type === 'ks_tile') {
                        var item_view = self._ksRenderDashboardTile(items[i])
                        if (items[i].id in self.gridstackConfig) {
                             self.grid.addWidget($(item_view)[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:true,minW:2,maxW:null,minH:2,maxH:null,id:items[i].id});
                        } else {
                             self.grid.addWidget($(item_view)[0], {x:0, y:0, w:4, h:2,autoPosition:true,minW:2,maxW:null,minH:2,maxH:2,id:items[i].id});
                        }
                    } else if (items[i].ks_dashboard_item_type === 'ks_list_view') {
                        self._renderListView(items[i], self.grid)
                    }else if (items[i].ks_dashboard_item_type === 'ks_kpi') {
                        var kpi_preview = self.renderKpi(items[i], self.grid)
                        if (items[i].id in self.gridstackConfig) {
                            self.grid.addWidget($kpi_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:true,minW:2,maxW:null,minH:2,maxH:null,id:items[i].id});
                        } else {
                             self.grid.addWidget($kpi_preview[0], {x:0, y:0, w:3, h:2,autoPosition:true,minW:2,maxW:null,minH:2,maxH:null,id:items[i].id});
                        }

                    }else {
                        self._renderGraph(items[i], self.grid)
                    }
                }
            }
        },

        _ksMainBodyStyle: function(ks_rgba_background_color, ks_rgba_font_color, tile){
            var background_style = "background-color:" + ks_rgba_background_color + ";color : " + ks_rgba_font_color + ";";
            var ks_rgba_dark_background_color_l2 = this._ks_get_rgba_format(this.ks_get_dark_color(tile.ks_background_color.split(',')[0], tile.ks_background_color.split(',')[1], -10));
            var style_image_body_l2 = "background-color:" + ks_rgba_dark_background_color_l2 + ";";
            return {
            'background_style': background_style,
            'style_image_body_l2': style_image_body_l2
                    };
        },

        _ksRenderDashboardTile: function(tile) {
            var self = this;
            var ks_container_class = 'grid-stack-item';
            var ks_inner_container_class = 'grid-stack-item-content';
            var ks_icon_url, item_view;
            var ks_rgba_background_color, ks_rgba_font_color, ks_rgba_default_icon_color,ks_rgba_button_color;
            var style_main_body, style_image_body_l2, style_domain_count_body, style_button_customize_body,
                style_button_delete_body;


            if (tile.ks_multiplier_active){
            var ks_record_count = tile.ks_record_count * tile.ks_multiplier
            if (tile.ks_unit){
            var ks_selection = tile.ks_unit_selection;
            if (ks_selection === 'monetary') {
            var ks_currency_id = tile.ks_currency_id;
            var ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_record_count, tile.ks_data_formatting, tile.ks_precision_digits);
            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
            var data_count = ks_data;
            } else{
            var ks_field = tile.ks_chart_unit;
            var data_count= ks_field+" "+KsGlobalFunction._onKsGlobalFormatter(ks_record_count, tile.ks_data_formatting, tile.ks_precision_digits);
            }}else {
            var data_count= KsGlobalFunction._onKsGlobalFormatter(ks_record_count, tile.ks_data_formatting, tile.ks_precision_digits);
            }
            var count = ks_record_count;
            }else{
            var ks_record_count = tile.ks_record_count
            if (tile.ks_unit){
            var ks_selection = tile.ks_unit_selection;
            if (ks_selection === 'monetary') {
            var ks_currency_id = tile.ks_currency_id;
            var ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_record_count, tile.ks_data_formatting, tile.ks_precision_digits);
            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
            var data_count = ks_data;
            } else{
            var ks_field = tile.ks_chart_unit;
            var data_count= ks_field+" "+KsGlobalFunction._onKsGlobalFormatter(ks_record_count, tile.ks_data_formatting, tile.ks_precision_digits);
            }}else {
            var data_count= KsGlobalFunction._onKsGlobalFormatter(ks_record_count, tile.ks_data_formatting, tile.ks_precision_digits);
            }
            var count = ks_record_count;
            }


            if (tile.ks_icon_select == "Custom") {
                if (tile.ks_icon[0]) {
                    ks_icon_url = 'data:image/' + (self.file_type_magic_word[tile.ks_icon[0]] || 'png') + ';base64,' + tile.ks_icon;
                } else {
                    ks_icon_url = false;
                }
            }


            tile.ksIsDashboardManager = self.ks_dashboard_data.ks_dashboard_manager;
            tile.ksIsUser = true;
            if (tile.ks_tv_play){
                tile.ksIsUser = false;
            }
            ks_rgba_background_color = self._ks_get_rgba_format(tile.ks_background_color);
            ks_rgba_font_color = self._ks_get_rgba_format(tile.ks_font_color);
            ks_rgba_default_icon_color = self._ks_get_rgba_format(tile.ks_default_icon_color);
            ks_rgba_button_color = self._ks_get_rgba_format(tile.ks_button_color);
            if (tile.ks_info){
                var ks_description = tile.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
//            style_main_body = "background-color:" + ks_rgba_background_color + ";color : " + ks_rgba_font_color + ";";
            style_main_body = this._ksMainBodyStyle(ks_rgba_background_color, ks_rgba_font_color, tile).background_style;
            switch (tile.ks_layout) {
                case 'layout1':
                    item_view = QWeb.render('ks_dashboard_item_layout1', {
                        item: tile,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_rgba_button_color:ks_rgba_button_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count,
                        count: count,
                        ks_info: ks_description,
                    });
                    break;

                case 'layout2':
//                    var ks_rgba_dark_background_color_l2 = self._ks_get_rgba_format(self.ks_get_dark_color(tile.ks_background_color.split(',')[0], tile.ks_background_color.split(',')[1], -10));
//                    style_image_body_l2 = "background-color:" + ks_rgba_dark_background_color_l2 + ";";
                    style_image_body_l2 = this._ksMainBodyStyle(ks_rgba_background_color, ks_rgba_font_color, tile).style_image_body_l2;
                    item_view = QWeb.render('ks_dashboard_item_layout2', {
                        item: tile,
                        style_image_body_l2: style_image_body_l2,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_rgba_button_color:ks_rgba_button_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count,
                        count: count,
                        ks_info: ks_description,

                    });
                    break;

                case 'layout3':
                    item_view = QWeb.render('ks_dashboard_item_layout3', {
                        item: tile,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_rgba_button_color:ks_rgba_button_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count,
                        count: count,
                        ks_info: ks_description,

                    });
                    break;

                case 'layout4':
                    style_main_body = "color : " + ks_rgba_font_color + ";border : solid;border-width : 1px;"
//                    style_image_body_l2 = "background-color:" + ks_rgba_background_color + ";";
                    style_image_body_l2 = this._ksMainBodyStyle(ks_rgba_background_color, ks_rgba_font_color, tile).background_style;
                    style_domain_count_body = "color:" + ks_rgba_background_color + ";";
                    item_view = QWeb.render('ks_dashboard_item_layout4', {
                        item: tile,
                        style_main_body: style_main_body,
                        style_image_body_l2: style_image_body_l2,
                        style_domain_count_body: style_domain_count_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_rgba_button_color:ks_rgba_button_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count,
                        count: count,
                        ks_info: ks_description,

                    });
                    break;

                case 'layout5':
                    item_view = QWeb.render('ks_dashboard_item_layout5', {
                        item: tile,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_rgba_button_color:ks_rgba_button_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count,
                        count: count,
                        ks_info: ks_description,

                    });
                    break;

                case 'layout6':
                    ks_rgba_default_icon_color = self._ks_get_rgba_format(tile.ks_default_icon_color);
                    item_view = QWeb.render('ks_dashboard_item_layout6', {
                        item: tile,
                        style_image_body_l2: style_image_body_l2,
                        style_main_body: style_main_body,
                        ks_icon_url: ks_icon_url,
                        ks_rgba_default_icon_color: ks_rgba_default_icon_color,
                        ks_rgba_button_color:ks_rgba_button_color,
                        ks_container_class: ks_container_class,
                        ks_inner_container_class: ks_inner_container_class,
                        ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                        data_count: data_count,
                        count: count,
                        ks_info: ks_description,

                    });
                    break;

                default:
                    item_view = QWeb.render('ks_dashboard_item_layout_default', {
                        item: tile
                    });
                    break;
            }


            return item_view
        },

        ks_container_option: function(chart_title, ksIsDashboardManager, ksIsUser, ks_dashboard_list, chart_id, chart_family, chart_type, ksChartColorOptions, ks_info, ks_company,ks_dashboard_item_type){
            var container_data = {
                ks_chart_title: chart_title,
                ksIsDashboardManager: ksIsDashboardManager,
                ksIsUser:ksIsUser,
                ks_dashboard_list: ks_dashboard_list,
                chart_id: chart_id,
                chart_family: chart_family,
                chart_type: chart_type,
                ksChartColorOptions: ksChartColorOptions,
                ks_info:ks_info,
                ks_company:ks_company,
                ks_dashboard_item_type:ks_dashboard_item_type
            }
            return container_data;
        },

        ks_set_selected_color_pallet: function($ks_gridstack_container, item){
            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('ks_date_filter_selected');
        },

        _renderGraph: function(item) {
            var self = this;
            var chart_data = JSON.parse(item.ks_chart_data);
            var isDrill = item.isDrill ? item.isDrill : false;
            var chart_id = item.id,
                chart_title = item.name;
            var chart_title = item.name;
            var chart_type = item.ks_dashboard_item_type.split('_')[1];
            switch (chart_type) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    var chart_family = "circle";
                    break;
                case "radar":
                    var chart_family = "circle";
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                case "area":
                    var chart_family = "square"
                    break;
                case "scatter":

                    var chart_family = "square"
                    break;
                default:
                    var chart_family = "none";
                    break;

            }
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }

            var container_data = this.ks_container_option(chart_title, self.ks_dashboard_data.ks_dashboard_manager, true, self.ks_dashboard_data.ks_dashboard_list, chart_id, chart_family, chart_type, this.ksChartColorOptions, ks_description, item.ks_company, item.ks_dashboard_item_type);

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_container', container_data)).addClass('ks_dashboarditem_id');
            self.ks_set_selected_color_pallet($ks_gridstack_container, item);
//            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('ks_date_filter_selected');

            var ksLayoutGridId = $(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id')
            if(ksLayoutGridId && ksLayoutGridId != 'ks_default'){
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_child_boards[parseInt(ksLayoutGridId)][1])
            }
            parseInt($(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id'))
            if (chart_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:true,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
                else{
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:false,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
//                self.grid.addWidget($ks_gridstack_container, self.gridstackConfig[chart_id].x, self.gridstackConfig[chart_id].y, self.gridstackConfig[chart_id].width, self.gridstackConfig[chart_id].height, false, 11, null, 3, null, chart_id);
            } else {
//                self.grid.addWidget($ks_gridstack_container, 0, 0, 13, 4, true, 11, null, 3, null, chart_id);
                  self.grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:5, h:4,autoPosition:true,minW:4,maxW:null,minH:3,maxH:null, id :chart_id});
            }
            self._renderChart($ks_gridstack_container, item);
        },

        ks_chart_color_pallet: function(gradient, setsCount, palette, item){
            var chartColors = [];
            var color_set = ['#F04F65', '#f69032', '#fdc233', '#53cfce', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7']
            if (palette !== "default") {
                //Get a sorted array of the gradient keys
                var gradientKeys = Object.keys(gradient);
                gradientKeys.sort(function(a, b) {
                    return +a - +b;
                });
                for (var i = 0; i < setsCount; i++) {
                    var gradientIndex = (i + 1) * (100 / (setsCount + 1)); //Find where to get a color from the gradient
                    for (var j = 0; j < gradientKeys.length; j++) {
                        var gradientKey = gradientKeys[j];
                        if (gradientIndex === +gradientKey) { //Exact match with a gradient key - just get that color
                            chartColors[i] = 'rgba(' + gradient[gradientKey].toString() + ')';
                            break;
                        } else if (gradientIndex < +gradientKey) { //It's somewhere between this gradient key and the previous
                            var prevKey = gradientKeys[j - 1];
                            var gradientPartIndex = (gradientIndex - prevKey) / (gradientKey - prevKey); //Calculate where
                            var color = [];
                            for (var k = 0; k < 4; k++) { //Loop through Red, Green, Blue and Alpha and calculate the correct color and opacity
                                color[k] = gradient[prevKey][k] - ((gradient[prevKey][k] - gradient[gradientKey][k]) * gradientPartIndex);
                                if (k < 3) color[k] = Math.round(color[k]);
                            }
                            chartColors[i] = 'rgba(' + color.toString() + ')';
                            break;
                        }
                    }
                }
            } else {
                for (var i = 0, counter = 0; i < setsCount; i++, counter++) {
                    if (counter >= color_set.length) counter = 0; // reset back to the beginning

                    chartColors.push(color_set[counter]);
                }

            }
            return chartColors;
        },

        _renderChart: function($ks_gridstack_container, item) {
            var self = this;
            var chart_data = JSON.parse(item.ks_chart_data);
            if (item.ks_chart_cumulative_field.length > 0){

                for (var i=0; i< chart_data.datasets.length; i++){
                    var ks_temp_com = 0
                    var data = []
                    var datasets = {}
                    if (chart_data.datasets[i].ks_chart_cumulative_field){
                        for (var j=0; j < chart_data.datasets[i].data.length; j++)
                            {
                                ks_temp_com = ks_temp_com + chart_data.datasets[i].data[j];
                                data.push(ks_temp_com);
                            }
                            datasets.label =  'Cumulative' + chart_data.datasets[i].label;
                            datasets.data = data;
                            if (item.ks_chart_cumulative){
                                datasets.type =  'line';
                            }
                            chart_data.datasets.push(datasets);
                    }
                }
            }
            if (item.ks_as_of_now){
                   for (var i=0; i< chart_data.datasets.length; i++){
                        if (chart_data.datasets[i].ks_as_of_now){
                            var ks_temp_com = 0
                            var data = []
                            var datasets = {}
                            for (var j=0; j < chart_data.datasets[i].data.length; j++)
                                {
                                    ks_temp_com = ks_temp_com + chart_data.datasets[i].data[j];
                                    data.push(ks_temp_com);
                                }
                            chart_data.datasets[i].data = data.slice(-item.ks_record_data_limit)
                        } else{
                            chart_data.datasets[i].data = chart_data.datasets[i].data.slice(-item.ks_record_data_limit)
                        }
                    }

              chart_data['labels'] = chart_data['labels'].slice(-item.ks_record_data_limit)

            }
            if (item.ks_chart_is_cumulative && item.ks_chart_data_count_type == 'count' && item.ks_dashboard_item_type === 'ks_bar_chart' && chart_data.datasets[0] && chart_data.datasets[0].data && item.ks_chart_data_count_type !== 'ks_scatter_chart'){
                var ks_temp_com = 0
                var data = []
                var datasets = {}
                for (var j=0; j < chart_data.datasets[0].data.length; j++){
                        ks_temp_com = ks_temp_com + chart_data.datasets[0].data[j];
                        data.push(ks_temp_com);
                    }
                datasets.label =  'Cumulative' + chart_data.datasets[0].label;
                datasets.data = data;
                if (item.ks_chart_cumulative){
                    datasets.type =  'line';
                }
                chart_data.datasets.push(datasets);
            }
            var isDrill = item.isDrill ? item.isDrill : false;
            var chart_id = item.id,
                chart_title = item.name;
            var chart_title = item.name;
            var chart_type = item.ks_dashboard_item_type.split('_')[1];
            switch (chart_type) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    var chart_family = "circle";
                    break;
                case "radar":
                    var chart_family = "circle";
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                 case "area":
                    var chart_family = "square"
                    break;
                case "scatter":

                    var chart_family = "square"
                    break;
                default:
                    var chart_family = "none";
                    break;

            }
            $ks_gridstack_container.find('.ks_color_pallate').data({
                chartType: chart_type,
                chartFamily: chart_family
            }); {
                chartType: "pie"
            }
            var $ksChartContainer = $('<canvas id="ks_chart_canvas_id" data-chart-id=' + chart_id + '/>');
            $ks_gridstack_container.find('.card-body').append($ksChartContainer);
            if (!item.ks_show_records) {
                $ks_gridstack_container.find('.ks_dashboard_item_chart_info').hide();
            }
            item.$el = $ks_gridstack_container;
            if (chart_family === "circle") {
                if (chart_data && chart_data['labels'].length > 30) {
                    $ks_gridstack_container.find(".ks_dashboard_color_option").remove();
                    $ks_gridstack_container.find(".card-body").empty().append($("<div style='font-size:20px;'>Too many records for selected Chart Type. Consider using <strong>Domain</strong> to filter records or <strong>Record Limit</strong> to limit the no of records under <strong>30.</strong>"));
                    return;
                }
            }

            if (chart_data["ks_show_second_y_scale"] && item.ks_dashboard_item_type === 'ks_bar_chart') {
                var scales = {}
                scales.yAxes = [{
                        type: "linear",
                        display: true,
                        position: "left",
                        id: "y-axis-0",
                        gridLines: {
                            display: true
                        },
                        labels: {
                            show: true,
                        }
                    },
                    {
                        type: "linear",
                        display: true,
                        position: "right",
                        id: "y-axis-1",
                        labels: {
                            show: true,
                        },
                        ticks: {
                            beginAtZero: true,
                            callback: function(value, index, values) {
                                var ks_selection = chart_data.ks_selection;
                                if (ks_selection === 'monetary') {
                                    var ks_currency_id = chart_data.ks_currency;
                                    var ks_data = value;
                                    ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                                    ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                                   return ks_data;
                                } else if (ks_selection === 'custom') {
                                    var ks_field = chart_data.ks_field;
                                    return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                                } else {
                                   return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                                }
                            },
                        }
                    }
                ]
            }
            var chart_plugin = [];
            if (item.ks_show_data_value) {
                chart_plugin.push(ChartDataLabels);
            }
            if (item.ks_dashboard_item_type =="ks_scatter_chart"){
            var scatter_data = []
            for (let i = 0 ; i<chart_data['labels'].length ; i++){
                scatter_data.push({"label":chart_data['labels'][i],"data":[{'x':chart_data['labels'][i],'y':chart_data.datasets[0].data[i]}]})
            }
            Object.assign(chart_data.datasets,scatter_data)
            }
//            if (item.ks_data_label_type == 'value'){
////                Chart empty dataset fixed in last commit
//                if(chart_data.datasets.length > 0){
////                    for(let i=0;i<chart_data.datasets.length;i++){
////                        chart_data.datasets[i]["ks_data_label_type"] = 'value';
////                    }
//                    chart_data.datasets[0]["ks_data_label_type"] = 'value';
//                }
//            }
            var ksMyChart = new Chart($ksChartContainer[0], {
                type: chart_type === "area" ? "line" : chart_type,
                plugins: chart_plugin,
                data: {
                    labels: chart_data['labels'],
                    groupByIds: chart_data['groupByIds'],
                    domains: chart_data['domains'],
                    datasets: chart_data.datasets,
                },
                options: {
                    maintainAspectRatio: false,
                    responsiveAnimationDuration: 1000,
                    animation: {
                        easing: 'easeInQuad',
                    },
                   legend: {
                            display: item.ks_hide_legend
                        },
                    scales: scales,
                   layout: {
                        padding: {
                        bottom: 0,
                   }
                },
                plugins: {
                    datalabels: {
                        backgroundColor: function(context) {
                            return context.dataset.backgroundColor;
                        },
                        borderRadius: 4,
                        color: 'white',
                        font: {
                            weight: 'bold'
                        },
                        anchor: 'right',
                        textAlign: 'center',
                        display: 'auto',
                        clamp: true,
                        formatter: function(value, ctx) {
                            let sum = 0;
                            let dataArr = ctx.dataset.data;
                            dataArr.map(data => {
                                sum += data;
                            });
                            let percentage = sum === 0 ? 0 + "%" : (value * 100 / sum).toFixed(2) + "%";
                            if (item.ks_data_label_type == 'value'){
                                percentage = value;
                                var ks_selection = chart_data.ks_selection;
                                if (ks_selection === 'monetary') {
                                    var ks_currency_id = chart_data.ks_currency;
                                    var ks_data = value;
                                    ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                                    ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                                   percentage = ks_data;
                                } else if (ks_selection === 'custom') {
                                    var ks_field = chart_data.ks_field;
                                    percentage = KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                                } else {
                                   percentage = KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                                }
                            }
                            return percentage;
                        },
                    },
                },

                }
            });

            this.chart_container[chart_id] = ksMyChart;
            if (chart_data && chart_data["datasets"].length > 0) self.ksChartColors(item.ks_chart_item_color, ksMyChart, chart_type, chart_family, item.ks_bar_chart_stacked, item.ks_semi_circle_chart, item.ks_show_data_value, chart_data, item);

        },

        ksHideFunction: function(options, item, ksChartFamily, chartType) {
            return options;
        },

        ksChartColors: function(palette, ksMyChart, ksChartType, ksChartFamily, stack, semi_circle, ks_show_data_value, chart_data, item) {
            var self = this;
            var currentPalette = "cool";
            if (!palette) palette = currentPalette;
            currentPalette = palette;

            /*Gradients
              The keys are percentage and the values are the color in a rgba format.
              You can have as many "color stops" (%) as you like.
              0% and 100% is not optional.*/
            var gradient;
            switch (palette) {
                case 'cool':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [220, 237, 200, 1],
                        45: [66, 179, 213, 1],
                        65: [26, 39, 62, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;
                case 'warm':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [254, 235, 101, 1],
                        45: [228, 82, 27, 1],
                        65: [77, 52, 47, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;
                case 'neon':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [255, 236, 179, 1],
                        45: [232, 82, 133, 1],
                        65: [106, 27, 154, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;

                case 'default':
                    var color_set = ['#F04F65', '#f69032', '#fdc233', '#53cfce', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7']
            }

            //Find datasets and length
            var chartType = ksMyChart.config.type;
            switch (chartType) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    if (ksMyChart.config.data.datasets[0]){
                        var datasets = ksMyChart.config.data.datasets[0];
                        var setsCount = datasets.data.length;
                    }
                    break;
                case "radar":
                    if (ksMyChart.config.data.datasets[0]){
                        var datasets = ksMyChart.config.data.datasets[0];
                        var setsCount = datasets.data.length;
                    }
                    break;

                case "bar":
                case "horizontalBar":
                case "line":
                case "scatter":

                    if (ksMyChart.config.data.datasets[0]){
                        var datasets = ksMyChart.config.data.datasets;
                        var setsCount = datasets.length;
                    }
                    break;
            }

            //Calculate colors
//            var chartColors = [];
//
//            if (palette !== "default") {
//                //Get a sorted array of the gradient keys
//                var gradientKeys = Object.keys(gradient);
//                gradientKeys.sort(function(a, b) {
//                    return +a - +b;
//                });
//                for (var i = 0; i < setsCount; i++) {
//                    var gradientIndex = (i + 1) * (100 / (setsCount + 1)); //Find where to get a color from the gradient
//                    for (var j = 0; j < gradientKeys.length; j++) {
//                        var gradientKey = gradientKeys[j];
//                        if (gradientIndex === +gradientKey) { //Exact match with a gradient key - just get that color
//                            chartColors[i] = 'rgba(' + gradient[gradientKey].toString() + ')';
//                            break;
//                        } else if (gradientIndex < +gradientKey) { //It's somewhere between this gradient key and the previous
//                            var prevKey = gradientKeys[j - 1];
//                            var gradientPartIndex = (gradientIndex - prevKey) / (gradientKey - prevKey); //Calculate where
//                            var color = [];
//                            for (var k = 0; k < 4; k++) { //Loop through Red, Green, Blue and Alpha and calculate the correct color and opacity
//                                color[k] = gradient[prevKey][k] - ((gradient[prevKey][k] - gradient[gradientKey][k]) * gradientPartIndex);
//                                if (k < 3) color[k] = Math.round(color[k]);
//                            }
//                            chartColors[i] = 'rgba(' + color.toString() + ')';
//                            break;
//                        }
//                    }
//                }
//            } else {
//                for (var i = 0, counter = 0; i < setsCount; i++, counter++) {
//                    if (counter >= color_set.length) counter = 0; // reset back to the beginning
//
//                    chartColors.push(color_set[counter]);
//                }
//            }
            var chartColors = this.ks_chart_color_pallet(gradient, setsCount, palette, item);
            var datasets = ksMyChart.config.data.datasets;
            var options = ksMyChart.config.options;

            options.legend.labels.usePointStyle = true;
            if (ksChartFamily == "circle") {
                if (ks_show_data_value) {
                    options.legend.position = 'bottom';
                    options.layout.padding.top = 10;
                    options.layout.padding.bottom = 20;
                    options.layout.padding.left = 20;
                    options.layout.padding.right = 20;
                } else {
                    options.legend.position = 'top';
                }

                options = self.ksHideFunction(options, item, ksChartFamily, chartType);

                options.plugins.datalabels.align = 'center';
                options.plugins.datalabels.anchor = 'end';
                options.plugins.datalabels.borderColor = 'white';
                options.plugins.datalabels.borderRadius = 25;
                options.plugins.datalabels.borderWidth = 2;
                options.plugins.datalabels.clamp = true;
                options.plugins.datalabels.clip = false;

                options.tooltips.callbacks = {
                    title: function(tooltipItem, data) {
                        var ks_self = self;
                        var k_amount = data.datasets[tooltipItem[0].datasetIndex]['data'][tooltipItem[0].index];
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            k_amount = KsGlobalFunction.ks_monetary(k_amount, ks_currency_id);
                            return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            //                                                        ks_type = field_utils.format.char(ks_field);
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,item.ks_precision_digits]});
                            return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount + " " + ks_field;
                        } else {
                            k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,item.ks_precision_digits]});
                            return data.datasets[tooltipItem[0].datasetIndex]['label'] + " : " + k_amount
                        }
                    },
                    label: function(tooltipItem, data) {
                        return data.labels[tooltipItem.index];
                    },
                }
                for (var i = 0; i < datasets.length; i++) {
                    if (chartType == "radar"){
                        datasets[i].borderColor = chartColors[i];

                        datasets[i]['datalabels'] = {
                                    backgroundColor: chartColors,
                                }
                    } else {
                        datasets[i].backgroundColor = chartColors;
                        datasets[i].borderColor = "rgba(255,255,255,1)";
                    }

                    switch (ksChartType) {
                        case "radar":
                            datasets[i].borderColor = chartColors[i];
                            break;
                    }
                }
                if (semi_circle && (chartType === "pie" || chartType === "doughnut")) {
                    options.rotation = 1 * Math.PI;
                    options.circumference = 1 * Math.PI;
                }
            } else if (ksChartFamily == "square") {
                options = self.ksHideFunction(options, item, ksChartFamily, chartType);

                options.scales.xAxes[0].gridLines.display = false;
                options.scales.yAxes[0].ticks.beginAtZero = true;

                options.plugins.datalabels.align = 'end';

                options.plugins.datalabels.formatter = function(value, ctx) {
                    var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            var ks_data = value;
                            ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                           return ks_data;
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                        } else {
                           return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                        }
                };

                if (chartType === "line") {
                    options.plugins.datalabels.backgroundColor = function(context) {
                        return context.dataset.borderColor;
                    };
                }

                if (chartType === "horizontalBar") {
                    options.scales.xAxes[0].ticks.callback = function(value, index, values) {
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            var ks_data = value;
                            ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                           return ks_data;
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                        } else {
                           return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                        }
                    }
                    options.scales.xAxes[0].ticks.beginAtZero = true;
                } else {
                    options.scales.yAxes[0].ticks.callback = function(value, index, values) {
                        var ks_selection = chart_data.ks_selection;
                        if (ks_selection === 'monetary') {
                            var ks_currency_id = chart_data.ks_currency;
                            var ks_data = value;
                            ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_data, item.ks_data_formatting, item.ks_precision_digits);
                            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
                           return ks_data;
                        } else if (ks_selection === 'custom') {
                            var ks_field = chart_data.ks_field;
                            return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits) + ' ' + ks_field;

                        } else {
                           return KsGlobalFunction._onKsGlobalFormatter(value, item.ks_data_formatting, item.ks_precision_digits);
                        }
                    }
                }
                if (this.chart_type !== 'scatter'){
                    options.tooltips.callbacks = {
                        label: function(tooltipItem, data) {
                            var ks_self = self;
                            var k_amount = data.datasets[tooltipItem.datasetIndex]['data'][tooltipItem.index];
                            var ks_selection = chart_data.ks_selection;
                            if (ks_selection === 'monetary') {
                                var ks_currency_id = chart_data.ks_currency;
                                k_amount = KsGlobalFunction.ks_monetary(k_amount, ks_currency_id);
                                return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount
                            } else if (ks_selection === 'custom') {
                                var ks_field = chart_data.ks_field;
                                // ks_type = field_utils.format.char(ks_field);
                                k_amount = field_utils.format.float(k_amount, Float64Array, {digits:[0,item.ks_precision_digits]});
                                return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount + " " + ks_field;
                            } else {
                                k_amount = field_utils.format.float(k_amount, Float64Array,{digits:[0,item.ks_precision_digits]});
                                return data.datasets[tooltipItem.datasetIndex]['label'] + " : " + k_amount
                            }
                        }
                    }
                }

                for (var i = 0; i < datasets.length; i++) {
                    switch (ksChartType) {
                        case "bar":
                        case "horizontalBar":
                            if (datasets[i].type && datasets[i].type == "line") {
                                datasets[i].borderColor = chartColors[i];
                                datasets[i].backgroundColor = "rgba(255,255,255,0)";
                                datasets[i]['datalabels'] = {
                                    backgroundColor: chartColors[i],
                                }
                            } else {
                                datasets[i].backgroundColor = chartColors[i];
                                datasets[i].borderColor = "rgba(255,255,255,0)";
                                options.scales.xAxes[0].stacked = stack;
                                options.scales.yAxes[0].stacked = stack;
                            }
                            break;
                        case "scatter":
                            datasets[i].backgroundColor = chartColors[i];
                            datasets[i]['datalabels'] = {
                                backgroundColor: chartColors[i],
                            }
                            break;
                        case "line":
                            datasets[i].borderColor = chartColors[i];
                            datasets[i].backgroundColor = "rgba(255,255,255,0)";
                            break;
                        case "area":
                            datasets[i].borderColor = chartColors[i];
                            break;
                    }
                }

            }
            ksMyChart.update();
        },

        onChartCanvasClick: function(evt) {

            var self = this;
//            $(self.$el.find('.ks_pager')).addClass('d-none');
            if (evt.currentTarget.classList.value !== 'ks_list_canvas_click') {
                var item_id = evt.currentTarget.dataset.chartId;
                if (item_id in self.ksUpdateDashboard) {
                    clearInterval(self.ksUpdateDashboard[item_id]);
                    delete self.ksUpdateDashboard[item_id]
                }
                var myChart = self.chart_container[item_id];
                var activePoint = myChart.getElementAtEvent(evt)[0];
                if (activePoint) {
                    var item_data = self.ks_dashboard_data.ks_item_data[item_id];
                    var groupBy = JSON.parse(item_data["ks_chart_data"])['groupby'];
                    if (activePoint._chart.data.domains) {
                        var sequnce = item_data.sequnce ? item_data.sequnce : 0;

                        var domain = activePoint._chart.data.domains[activePoint._index]
                        if (item_data.max_sequnce != 0 && sequnce < item_data.max_sequnce) {
                            self._rpc({
                                model: 'ks_dashboard_ninja.item',
                                method: 'ks_fetch_drill_down_data',
                                args: [item_id, domain, sequnce]
                            }).then(function(result) {
                                self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                                self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                                if (result.ks_chart_data) {
                                    self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                                    self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                                    if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                                        self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                                    } else {
                                        self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                                        self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                                    }
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');

                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                                    var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                                    if (item_data.ks_dashboard_item_type === 'ks_flower_view'){
                                        self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                        self.ksrenderflowerchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                                    }else if(item_data.ks_dashboard_item_type == 'ks_radialBar_chart'){
                                        self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                        self.ksrenderradialchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                                    }else if(item_data.ks_dashboard_item_type == 'ks_bullet_chart'){
                                        self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                        self.ksrenderbulletchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                                    }else if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                                        self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                        self.ksrenderfunnelchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                                    }else{
                                        self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]), item_data);
                                    }
                                } else {
                                    if ('domains' in self.ks_dashboard_data.ks_item_data[item_id]) {
                                        self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                                    } else {
                                        self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                                        self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                                    }
                                    self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                                    self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                                    self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                                    self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                                    self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';

                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');

                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');
                                    var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                                    var $container = self.renderListViewData(item_data);
                                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container).addClass('ks_overflow');
                                }
                            });
                        } else {
                        if (item_data.action) {
                                if (!item_data.ks_is_client_action){
                                    var action = Object.assign({}, item_data.action);
                                    if (action.view_mode.includes('tree')) action.view_mode = action.view_mode.replace('tree', 'list');
                                    for (var i = 0; i < action.views.length; i++) action.views[i][1].includes('tree') ? action.views[i][1] = action.views[i][1].replace('tree', 'list') : action.views[i][1];
                                    action['domain'] = domain || [];
                                    action['search_view_id'] = [action.search_view_id, 'search']
                                }else{
                                    var action = Object.assign({}, item_data.action[0]);
                                    if (action.params){
                                        action.params.default_active_id || 'mailbox_inbox';
                                        }else{
                                            action.params = {
                                            'default_active_id': 'mailbox_inbox'
                                            };
                                            action.context = {}
                                            action.context.params = {
                                            'active_model': false
                                            };
                                        }
                                }
                            } else {
                                var action = {
                                    name: _t(item_data.name),
                                    type: 'ir.actions.act_window',
                                    res_model: item_data.ks_model_name,
                                    domain: domain || [],
                                    context: {
                                        'group_by': groupBy ? groupBy:false ,
                                    },
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    view_mode: 'list',
                                    target: 'current',
                                }
                            }
                            if (item_data.ks_show_records) {


                                if (item_data.ks_is_client_action){
                                    self.__parentedParent.actionService.doAction(action,{})
                                }else{
                                    self.do_action(action, {
                                        on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                                    });
                                }
                            }
                        }
                    }
                }
            } else {
                var item_id = $(evt.target).parent().data().itemId;
                if (this.ksUpdateDashboard[item_id]) {
                    clearInterval(this.ksUpdateDashboard[item_id]);
                    delete self.ksUpdateDashboard[item_id];
                }
                var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                if (self.ks_dashboard_data.ks_item_data[item_id].max_sequnce) {

                    var sequence = item_data.sequnce ? item_data.sequnce : 0

                    var domain = $(evt.target).parent().data().domain;

                    if ($(evt.target).parent().data().last_seq !== sequence) {
                        self._rpc({
                            model: 'ks_dashboard_ninja.item',
                            method: 'ks_fetch_drill_down_data',
                            args: [item_id, domain, sequence]
                        }).then(function(result) {
                            if (result.ks_list_view_data) {
                                if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                                    self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                                } else {
                                    self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                                    self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                                }
                                self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                                self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
                                self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                                var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                                var $container = self.renderListViewData(item_data);
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
                            } else {
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                                self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                                self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                                if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                                    self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                                } else {
                                    self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                                    self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                                }
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                                var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                                self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]), item_data);
                            }
                        });
                    }
                }
            }
            evt.stopPropagation();
        },

        ksOnDrillUp: function(e) {
            var self = this;
            var item_id = e.currentTarget.dataset.itemId;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var domain;
            if(item_data) {

                if ('domains' in item_data) {
                    domain = item_data['domains'][item_data.sequnce - 1] ? item_data['domains'][item_data.sequnce - 1] : []
                    var sequnce = item_data.sequnce - 2;
                    if (sequnce >= 0) {
                        self._rpc({
                            model: 'ks_dashboard_ninja.item',
                            method: 'ks_fetch_drill_down_data',
                            args: [item_id, domain, sequnce]
                        }).then(function(result) {
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                            self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                            if (result.ks_chart_type)  self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                            if (result.ks_chart_data) {
                                var item_data = self.ks_dashboard_data.ks_item_data[item_id];
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                                self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]), item_data);

                            } else {
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                                self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
                                var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                                var $container = self.renderListViewData(item_data);
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                                $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
                            }

                        });

                    } else {
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").addClass('d-none');
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").addClass('d-sm-block ');
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").removeClass('d-none');
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").removeClass('d-none')
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").removeClass('d-none')
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").removeClass('d-none')
                        self.ksFetchChartItem(item_id)
//                        $(self.$el.find('.ks_pager')).removeClass('d-none');
                        var updateValue = self.ks_dashboard_data.ks_set_interval;
                        if (updateValue) {
                            var updateinterval = setInterval(function() {
                                self.ksFetchChartItem(item_id)
                            }, updateValue);
                            self.ksUpdateDashboard[item_id] = updateinterval;
                        }
                    }

                } else {
                    if(!domain){
                    $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").addClass('d-none');
                }

                }
            }

            e.stopPropagation();
        },

        ksFetchChartItem: function(id) {
            var self = this;
            var item_data = self.ks_dashboard_data.ks_item_data[id];

            return self._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_item',
                args: [
                    [item_data.id], self.ks_dashboard_id, self.ksGetParamsForItemFetch(id)
                ],
                context: self.getContext(),
            }).then(function(new_item_data) {
                this.ks_dashboard_data.ks_item_data[id] = new_item_data[id];
                $(self.$el.find(".grid-stack-item[gs-id=" + id + "]").children()[0]).find(".card-body").empty();
                var item_data = self.ks_dashboard_data.ks_item_data[id]
                if (item_data.ks_list_view_data) {
                    var item_view = $(self.$el.find(".grid-stack-item[gs-id=" + id + "]").children()[0]);
                    var $container = self.renderListViewData(item_data);
                    item_view.find(".card-body").append($container);
                    var ks_length = JSON.parse(item_data['ks_list_view_data']).data_rows.length
                    if (new_item_data["ks_list_view_type"] === "ungrouped" && JSON.parse(item_data['ks_list_view_data']).data_rows.length) {
                        item_view.find('.ks_pager').removeClass('d-none');
                        if (item.ks_record_count <= item.ks_pagination_limit) item_view.find('.ks_load_next').addClass('ks_event_offer_list');
                        item_view.find('.ks_value').text("1-" + JSON.parse(item_data['ks_list_view_data']).data_rows.length);
                    } else {
                        item_view.find('.ks_pager').addClass('d-none');
                    }
                }else if(item_data['ks_dashboard_item_type'] == 'ks_funnel_chart'){
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self.ksrenderfunnelchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_bullet_chart'){
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self. ksrenderbulletchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_flower_view'){
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self.ksrenderflowerchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_radialBar_chart'){
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                     var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                     self.ksrenderradialchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_map_view'){
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                     var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                     self.ksrendermapview(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else {
                    self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + id + "]").children()[0]), item_data);
                }
            }.bind(this));
        },

        onChartMoreInfoClick: function(evt) {
            var self = this;
            var item_id = evt.currentTarget.dataset.itemId;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var groupBy = item_data.ks_chart_groupby_type === 'relational_type' ? item_data.ks_chart_relation_groupby_name : item_data.ks_chart_relation_groupby_name + ':' + item_data.ks_chart_date_groupby;
            var domain = JSON.parse(item_data.ks_chart_data).previous_domain

            if (item_data.ks_show_records) {
                if (item_data.action) {

                    if (!item_data.ks_is_client_action){
                        var action = Object.assign({}, item_data.action);
                        if (action.view_mode.includes('tree')) action.view_mode = action.view_mode.replace('tree', 'list');
                            for (var i = 0; i < action.views.length; i++) action.views[i][1].includes('tree') ? action.views[i][1] = action.views[i][1].replace('tree', 'list') : action.views[i][1];
                                action['domain'] = item_data.ks_domain || [];
                                action['search_view_id'] = [action.search_view_id, 'search']
                        }else{
                            var action = Object.assign({}, item_data.action[0]);
                            if (action.params){
                                action.params.default_active_id || 'mailbox_inbox';
                                }else{
                                    action.params = {
                                    'default_active_id': 'mailbox_inbox'
                                    }
                                    action.context = {}
                                    action.context.params = {
                                    'active_model': false
                                    };
                                }
                            }
                } else {
                    var action = {
                        name: _t(item_data.name),
                        type: 'ir.actions.act_window',
                        res_model: item_data.ks_model_name,
                        domain: domain || [],
                        context: {
                            'group_by': groupBy ? groupBy:false ,
                        },
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        view_mode: 'list',
                        target: 'current',
                    }
                }
                self.do_action(action, {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                });
            }
        },

        _ksRenderNoItemView: function() {
            $('.ks_dashboard_items_list').remove();
            var self = this;
            $(QWeb.render('ksNoItemView')).appendTo(self.$el)

        },

        _ksRenderEditMode: function() {

            var self = this;
            self.ks_mode = 'edit';
            self.ks_remove_update_interval();

            $('#ks_dashboard_title_input').val(self.ks_dashboard_data.name);

            $('.ks_am_element').addClass("ks_hide");
            $('.ks_em_element').removeClass("ks_hide");
            $('.ks_dashboard_print_pdf').addClass("ks_hide");

            self.$el.find('.ks_item_click').addClass('ks_item_not_click').removeClass('ks_item_click');
            self.$el.find('.ks_dashboard_item').removeClass('ks_dashboard_item_header_hover');
            self.$el.find('.ks_dashboard_item_header').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_item_l2').removeClass('ks_dashboard_item_header_hover');
            self.$el.find('.ks_dashboard_item_header_l2').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_item_l5').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_item_button_container').removeClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_link').addClass("ks_hide")
            self.$el.find('.ks_dashboard_top_settings').addClass("ks_hide")
            self.$el.find('.ks_dashboard_edit_mode_settings').removeClass("ks_hide")

            // Adding Chart grab able cals
            self.$el.find('.ks_start_tv_dashboard').addClass('ks_hide');
            self.$el.find('.ks_chart_container').addClass('ks_item_not_click');
            self.$el.find('.ks_list_view_container').addClass('ks_item_not_click');

            if (self.grid) {
                self.grid.enable();
            }
        },


        _ksRenderActiveMode: function() {
            var self = this
            self.ks_mode = 'active';

            if (self.grid && $('.grid-stack').data('gridstack')) {
                $('.grid-stack').data('gridstack').disable();
            }

            if (self.ks_dashboard_data.ks_child_boards) {
//                var dash_name = $('ul[id="ks_dashboard_layout_dropdown_container"] li[class="ks_dashboard_layout_event ks_layout_selected"] span').text()
                var $layout_container = $(QWeb.render('ks_dn_layout_container', {
                    ks_selected_board_id: self.ks_dashboard_data.ks_selected_board_id,
                    ks_child_boards: self.ks_dashboard_data.ks_child_boards,
                    ks_multi_layout: self.ks_dashboard_data.multi_layouts,
                    ks_dash_name: self.ks_dashboard_data.name
                }));
                $('#ks_dashboard_title .ks_am_element').replaceWith($layout_container);
                $('#ks_dashboard_title_label').replaceWith($layout_container);
            } else {
                $('#ks_dashboard_title_label').text(self.ks_dashboard_data.name);
            }

            $('#ks_dashboard_title_label').text(self.ks_dashboard_data.name);

            $('.ks_am_element').removeClass("ks_hide");
            $('.ks_em_element').addClass("ks_hide");
            $('.ks_dashboard_print_pdf').removeClass("ks_hide");
            if (self.ks_dashboard_data.ks_item_data) $('.ks_am_content_element').removeClass("ks_hide");

            self.$el.find('.ks_item_not_click').addClass('ks_item_click').removeClass('ks_item_not_click')
            self.$el.find('.ks_dashboard_item').addClass('ks_dashboard_item_header_hover')
            self.$el.find('.ks_dashboard_item_header').addClass('ks_dashboard_item_header_hover')

            self.$el.find('.ks_dashboard_item_l2').addClass('ks_dashboard_item_header_hover')
            self.$el.find('.ks_dashboard_item_header_l2').addClass('ks_dashboard_item_header_hover')

            //      For layout 5
            self.$el.find('.ks_dashboard_item_l5').addClass('ks_dashboard_item_header_hover')


            self.$el.find('.ks_dashboard_item_button_container').addClass('ks_dashboard_item_header_hover');

            self.$el.find('.ks_dashboard_top_settings').removeClass("ks_hide")
            self.$el.find('.ks_dashboard_edit_mode_settings').addClass("ks_hide")

            self.$el.find('.ks_start_tv_dashboard').removeClass('ks_hide');
            self.$el.find('.ks_chart_container').removeClass('ks_item_not_click ks_item_click');
            self.$el.find('.ks_list_view_container').removeClass('ks_item_click');

            self.ks_set_update_interval();
            self.grid.commit();
        },

        _ksToggleEditMode: function() {
            var self = this
            if (self.ksDashboardEditMode) {
                self._ksRenderActiveMode()
                self.ksDashboardEditMode = false
            } else if (!self.ksDashboardEditMode) {
                self._ksRenderEditMode()
                self.ksDashboardEditMode = true
            }

        },

        onAddItemTypeClick: function(e) {
            var self = this;
            if (e.currentTarget.dataset.item !== "ks_json") {
                self.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'ks_dashboard_ninja.item',
                    view_id: 'ks_dashboard_ninja_list_form_view',
                    views: [
                        [false, 'form']
                    ],
                    target: 'current',
                    context: {
                        'ks_dashboard_id': self.ks_dashboard_id,
                        'ks_dashboard_item_type': e.currentTarget.dataset.item,
                        'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                        'form_view_initial_mode': 'edit',
                        'ks_set_interval': self.ks_dashboard_data.ks_set_interval,
                        'ks_data_formatting':self.ks_dashboard_data.ks_data_formatting,
                    },
                }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                });
            } else {
                self.ksImportItemJson(e);
            }
        },

        ksImportItemJson: function(e) {
            var self = this;
            $('.ks_input_import_item_button').click();
        },

        ksImportItem: function(e) {
            var self = this;
            var fileReader = new FileReader();
            fileReader.onload = function() {
                $('.ks_input_import_item_button').val('');
//                framework.blockUI();
                self._rpc({
                    model: 'ks_dashboard_ninja.board',
                    method: 'ks_import_item',
                    args: [self.ks_dashboard_id],
                    kwargs: {
                        file: fileReader.result,
                        dashboard_id: self.ks_dashboard_id
                    }
                }).then(function(result) {
                    if (result === "Success") {

                        $.when(self.ks_fetch_data()).then(function() {
                            $.when(self.ks_fetch_items_data()).then(function(result){
                                self.ksRenderDashboard();
                            });

//                            framework.unblockUI();
                        });
                    }
                });
            };
            fileReader.readAsText($('.ks_input_import_item_button').prop('files')[0]);
        },

        _onKsAddLayoutClick: function() {
            var self = this;

            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.item',
                view_id: 'ks_dashboard_ninja_list_form_view',
                views: [
                    [false, 'form']
                ],
                target: 'current',
                context: {
                    'ks_dashboard_id': self.ks_dashboard_id,
                    'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                    'form_view_initial_mode': 'edit',
                },
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },

        _onKsEditLayoutClick: function() {
            var self = this;
            self.grid.setStatic(false);
            self._ksRenderEditMode();
        },

        _onKsSaveLayoutClick: function() {
            this.grid.setStatic(true)
            var self = this;
            //        Have  to save dashboard here
            var dashboard_title = $('#ks_dashboard_title_input').val();
            if (dashboard_title != false && dashboard_title != 0 && dashboard_title !== self.ks_dashboard_data.name) {
                self.ks_dashboard_data.name = dashboard_title;
                var model = 'ks_dashboard_ninja.board';
                var rec_id = self.ks_dashboard_id;

                if(this.ks_dashboard_data.ks_selected_board_id && this.ks_dashboard_data.ks_child_boards){
                    this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][0] = dashboard_title;
                    if (this.ks_dashboard_data.ks_selected_board_id !== 'ks_default'){
                        model = 'ks_dashboard_ninja.child_board';
                        rec_id = this.ks_dashboard_data.ks_selected_board_id;
                    }
                }
                this._rpc({
                    model: model,
                    method: 'write',
                    args: [rec_id, {
                        'name': dashboard_title
                    }],
                })
            }
            if (this.ks_dashboard_data.ks_item_data) self._ksSaveCurrentLayout();
            self._ksRenderActiveMode();
        },

        _onKsCreateLayoutClick: function() {
            var self = this;
            self.grid.setStatic(true)
            var dashboard_title = $('#ks_dashboard_title_input').val();
            if (dashboard_title ==="") {
                self.call('notification', 'notify', {
                    message: "Dashboard Name is required to save as New Layout.",
                    type: 'warning',
                });
            } else{
                if (!self.ks_dashboard_data.ks_child_boards){
                    self.ks_dashboard_data.ks_child_boards = {
                        'ks_default': [this.ks_dashboard_data.name, self.ks_dashboard_data.ks_gridstack_config]
                    }
                }
                this.ks_dashboard_data.name = dashboard_title;

                var grid_config = self.ks_get_current_gridstack_config();
                this._rpc({
                    model: 'ks_dashboard_ninja.board',
                    method: 'update_child_board',
                    args: ['create', self.ks_dashboard_id, {
                        "ks_gridstack_config": JSON.stringify(grid_config),
                        "ks_dashboard_ninja_id": self.ks_dashboard_id,
                        "name": dashboard_title,
                        "ks_active": true,
                        "company_id": self.ks_dashboard_data.ks_company_id,
                    }],
                }).then(function(res_id){
                    self.ks_update_child_board_value(dashboard_title, res_id, grid_config),
                    self._ksRenderActiveMode();
                    window.location.reload();
                });
            }
        },

        ks_update_child_board_value: function(dashboard_title, res_id, grid_config){
            var self = this;
            var child_board_id = res_id.toString();
            self.ks_dashboard_data.ks_selected_board_id = child_board_id;
            var update_data = {};
            update_data[child_board_id] = [dashboard_title, JSON.stringify(grid_config)];
            self.ks_dashboard_data.ks_child_boards = _.extend(update_data,self.ks_dashboard_data.ks_child_boards);
        },

        _onKsCancelLayoutClick: function() {
            var self = this;
            //        render page again
            $.when(self.ks_fetch_data()).then(function() {
                $.when(self.ks_fetch_items_data()).then(function(result){
                    self.ksRenderDashboard();
                    self.ks_set_update_interval();
                });
            });
        },

        _onKsItemClick: function(e) {
            var self = this;
            //  To Handle only allow item to open when not clicking on item
            if (self.ksAllowItemClick) {



                e.preventDefault();
                if (e.target.title != "Customize Item") {
                    var item_id = parseInt(e.currentTarget.firstElementChild.id);
                    var item_data = self.ks_dashboard_data.ks_item_data[item_id];
                    if (item_data && item_data.ks_show_records) {

                        if (item_data.action) {
                            if (!item_data.ks_is_client_action){
                                var action = Object.assign({}, item_data.action);
                                if (action.view_mode.includes('tree')) action.view_mode = action.view_mode.replace('tree', 'list');
                                for (var i = 0; i < action.views.length; i++) action.views[i][1].includes('tree') ? action.views[i][1] = action.views[i][1].replace('tree', 'list') : action.views[i][1];
                                action['domain'] = item_data.ks_domain || [];
                                action['search_view_id'] = [action.search_view_id, 'search']
                            }else{
                                var action = Object.assign({}, item_data.action[0]);
                                if (action.params){
                                    action.params.default_active_id || 'mailbox_inbox';
                                    }else{
                                        action.params = {
                                        'default_active_id': 'mailbox_inbox'
                                        }
                                        action.context = {}
                                        action.context.params = {
                                        'active_model': false
                                        };
                                    }
                            }

                        } else {
                            var action = {
                                name: _t(item_data.name),
                                type: 'ir.actions.act_window',
                                res_model: item_data.ks_model_name,
                                domain: item_data.ks_domain || "[]",
                                views: [
                                    [false, 'list'],
                                    [false, 'form']
                                ],
                                view_mode: 'list',
                                target: 'current',
                            }
                        }

                        if (item_data.ks_is_client_action){
                            self.__parentedParent.actionService.doAction(action,{})
                        }else{
                            self.do_action(action, {
                                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                            });
                        }
                    }
                }
            } else {
                self.ksAllowItemClick = true;
            }
        },

        _onKsItemCustomizeClick: function(e) {
            var self = this;
            var id = parseInt($($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0]).attr('gs-id'));
            self.ks_open_item_form_page(id);

            e.stopPropagation();
        },

        ks_open_item_form_page: function(id) {
            var self = this;
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.item',
                view_id: 'ks_dashboard_ninja_list_form_view',
                views: [
                    [false, 'form']
                ],
                target: 'current',
                context: {
                    'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                    'form_view_initial_mode': 'edit',
                },
                res_id: id
            }, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },


        // Note : this is exceptionally bind to this function.
        ksUpdateDashboardItem: function(ids) {
            var self = this;
            for (var i = 0; i < ids.length; i++) {

                var item_data = self.ks_dashboard_data.ks_item_data[ids[i]]
                if (item_data['ks_dashboard_item_type'] == 'ks_list_view') {
                    var item_view = self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]");
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    item_view.children().find('.ks_list_view_heading').prop('title', name);
                    item_view.children().find('.ks_list_view_heading').text(name);
                    item_view.find('.card-body').empty();
                    item_view.find('.ks_dashboard_item_drill_up').addClass('d-none')
                    item_view.find('.ks_dashboard_item_action_export').removeClass('d-none')
                    item_view.find('.ks_dashboard_quick_edit_action_popup ').removeClass('d-none')
                    item_view.find('.card-body').append(self.renderListViewData(item_data));
                    var rows = JSON.parse(item_data['ks_list_view_data']).data_rows;
                    var ks_length = rows ? rows.length : false;
                    if (ks_length) {
                        if (item_view.find('.ks_pager_name')) {
                            item_view.find('.ks_pager_name').empty();
                            var $ks_pager_container = QWeb.render('ks_pager_template', {
                                item_id: ids[i],
                                intial_count: item_data.ks_pagination_limit,
                                offset : 1
                            })
                            item_view.find('.ks_pager_name').append($($ks_pager_container));
                        }

                            if (ks_length < item_data.ks_pagination_limit) item_view.find('.ks_load_next').addClass('ks_event_offer_list');
                                item_view.find('.ks_value').text("1-" + JSON.parse(item_data['ks_list_view_data']).data_rows.length);

                            if (item_data.ks_record_data_limit == item_data.ks_pagination_limit || item_data.ks_record_count==item_data.ks_pagination_limit) {
                                item_view.find('.ks_load_next').addClass('ks_event_offer_list');
                            }
                    } else {
                        item_view.find('.ks_pager').addClass('d-none');
                    }
                } else if (item_data['ks_dashboard_item_type'] == 'ks_tile') {
                    var item_view = self._ksRenderDashboardTile(item_data);
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".ks_dashboard_item_hover").replaceWith($(item_view).find('.ks_dashboarditem_id'));
                } else if (item_data['ks_dashboard_item_type'] == 'ks_kpi') {
                    var item_view = self.renderKpi(item_data);
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".ks_dashboard_item_hover").replaceWith($(item_view).find('.ks_dashboarditem_id'));
                } else  if (item_data['ks_dashboard_item_type'] == 'ks_to_do'){
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").empty();
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").append(self.ksRenderToDoDashboardView(item_data)[0].children());
                }else if(item_data['ks_dashboard_item_type'] == 'ks_funnel_chart'){

                    if (item_data['ks_funnel_item_color']){
                         this._rpc({
                            model: 'ks_dashboard_ninja.item',
                            method: 'write',
                            args: [item_data.id, {
                                "ks_funnel_item_color": item_data['ks_funnel_item_color']
                            }],
                        }).then(function() {
                            item_data['ks_funnel_item_color'] = item_data['ks_funnel_item_color']
                        });
                    }
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self.ksrenderfunnelchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_bullet_chart'){

                    if (item_data['ks_funnel_item_color']){
                         this._rpc({
                            model: 'ks_dashboard_ninja.item',
                            method: 'write',
                            args: [item_data.id, {
                                "ks_funnel_item_color": item_data['ks_funnel_item_color']
                            }],
                        }).then(function() {
                            item_data['ks_funnel_item_color'] = item_data['ks_funnel_item_color']
                        });
                    }

                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self. ksrenderbulletchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_flower_view'){

                    if (item_data['ks_flower_item_color']){
                         this._rpc({
                            model: 'ks_dashboard_ninja.item',
                            method: 'write',
                            args: [item_data.id, {
                                "ks_flower_item_color": item_data['ks_flower_item_color']
                            }],
                        }).then(function() {
                            item_data['ks_flower_item_color'] = item_data['ks_flower_item_color']
                        });
                    }
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self.ksrenderflowerchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_radialBar_chart'){

                    if (item_data['ks_radial_item_color']){
                         this._rpc({
                            model: 'ks_dashboard_ninja.item',
                            method: 'write',
                            args: [item_data.id, {
                                "ks_radial_item_color": item_data['ks_radial_item_color']
                            }],
                        }).then(function() {
                            item_data['ks_radial_item_color'] = item_data['ks_radial_item_color']
                        });
                    }
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                     var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                     self.ksrenderradialchart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else if(item_data['ks_dashboard_item_type'] == 'ks_map_view'){
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                     var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                     self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                     self.ksrendermapview(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
                }else{
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").empty()
                    var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                    self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                    self._renderChart(self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]"), item_data);
                }

            }
            self.grid.setStatic(true);
        },

        _onKsDeleteItemClick: function(e) {
            var self = this;
            var item = $($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0])
            var id = parseInt($($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0]).attr('gs-id'));
            self.ks_delete_item(id, item);
            e.stopPropagation();
        },

        ks_delete_item: function(id, item) {
            var self = this;
            Dialog.confirm(this, (_t("Are you sure you want to remove this item?")), {
                confirm_callback: function() {

                    self._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'unlink',
                        args: [id],
                    }).then(function(result) {

                        // Clean Item Remove Process.
                        self.ks_remove_update_interval();
                        delete self.ks_dashboard_data.ks_item_data[id];
                        self.grid.removeWidget(item);
                        self.ks_set_update_interval();

                        if (Object.keys(self.ks_dashboard_data.ks_item_data).length > 0) {
                            self._ksSaveCurrentLayout();
                        }
                        else {
                            self._ksRenderNoItemView();
                            self.ksRenderDashboard();
                        }
                        $.when(self.ks_fetch_data()).then(function() {
                            $.when(self.ks_fetch_items_data()).then(function(){
                                self.ks_remove_update_interval();
                                self.ksRenderDashboard();
                                self.ks_set_update_interval();
                            });
                        });
                    });
                },
            });
        },
       ks_add_dashboard_item_on_empty: function(e){
       var self = this;
            if (e.currentTarget.dataset.item !== "ks_json") {
                self.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'ks_dashboard_ninja.item',
                    view_id: 'ks_dashboard_ninja_list_form_view',
                    views: [
                        [false, 'form']
                    ],
                    target: 'current',
                    context: {
                        'ks_dashboard_id': self.ks_dashboard_id,
                        'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                        'form_view_initial_mode': 'edit',
                    },
                }, {
                    on_reverse_breadcrumb: this.on_reverse_breadcrumb,
                });
            } else {
                self.ksImportItemJson(e);
            }
       },

        _ksSaveCurrentLayout: function() {
            var self = this;
            var grid_config = self.ks_get_current_gridstack_config();
            var model = 'ks_dashboard_ninja.child_board';
            var rec_id = self.ks_dashboard_data.ks_gridstack_config_id;
            self.ks_dashboard_data.ks_gridstack_config = JSON.stringify(grid_config);
            if(this.ks_dashboard_data.ks_selected_board_id && this.ks_dashboard_data.ks_child_boards){
                this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][1] = JSON.stringify(grid_config);
                if (this.ks_dashboard_data.ks_selected_board_id !== 'ks_default'){
                    rec_id = this.ks_dashboard_data.ks_selected_board_id;
                }
            }
            if (!config.device.isMobile) {
                this._rpc({
                model: model,
                method: 'write',
                args: [rec_id, {
                    "ks_gridstack_config": JSON.stringify(grid_config)
                }],
            });
            }
        },

        ks_get_current_gridstack_config: function(){
            var self = this;
            if (document.querySelector('.grid-stack') && document.querySelector('.grid-stack').gridstack){
                var items = document.querySelector('.grid-stack').gridstack.el.gridstack.engine.nodes;
            }
            var grid_config = {}

//            if (self.ks_dashboard_data.ks_gridstack_config && config.device.isMobile) {
//                _.extend(grid_config, JSON.parse(self.ks_dashboard_data.ks_gridstack_config))
//            }
            if (items){
                for (var i = 0; i < items.length; i++) {
                    grid_config[items[i].id] = {
                        'x': items[i].x,
                        'y': items[i].y,
                        'w': items[i].w,
                        'h': items[i].h,
                    }
                }
            }
            return grid_config;
        },

        _renderListView: function(item, grid) {
            var self = this;
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }

            var list_view_data = JSON.parse(item.ks_list_view_data),
                pager = true,
                item_id = item.id,
                data_rows = list_view_data.data_rows,
                length = data_rows ? data_rows.length: false,
                item_title = item.name,
                ks_info = ks_description;
            var $ksItemContainer = self.renderListViewData(item);
            var  ks_data_calculation_type = self.ks_dashboard_data.ks_item_data[item_id].ks_data_calculation_type
            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_list_view_container', {
                ks_chart_title: item_title,
                ksIsDashboardManager: self.ks_dashboard_data.ks_dashboard_manager,
                ksIsUser: true,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                item_id: item_id,
                count: '1-' + length,
                offset: 1,
                intial_count: length,
                ks_pager: pager,
                calculation_type: ks_data_calculation_type,
                ks_info: ks_info,
                ks_company:item.ks_company

            })).addClass('ks_dashboarditem_id');

            if (item.ks_pagination_limit < length  ) {
                $ks_gridstack_container.find('.ks_load_next').addClass('ks_event_offer_list');
            }
            if (length < item.ks_pagination_limit ) {
                $ks_gridstack_container.find('.ks_load_next').addClass('ks_event_offer_list');
            }
            if (item.ks_record_data_limit === item.ks_pagination_limit){
                   $ks_gridstack_container.find('.ks_load_next').addClass('ks_event_offer_list');
            }
            if (length == 0){
                $ks_gridstack_container.find('.ks_pager').addClass('d-none');
            }
            if (item.ks_pagination_limit==0){
            $ks_gridstack_container.find('.ks_pager_name').addClass('d-none');
            }

            $ks_gridstack_container.find('.card-body').append($ksItemContainer);
            if (item.ks_data_calculation_type === 'query' || item.ks_list_view_type === "ungrouped"){
                $ks_gridstack_container.find('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
            }
            item.$el = $ks_gridstack_container;
            if (item_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[item_id].x, y:self.gridstackConfig[item_id].y, w:self.gridstackConfig[item_id].w, h:self.gridstackConfig[item_id].h, autoPosition:true, minW:3, maxW:null, minH:3, maxH:null, id:item_id});
                }
                else{
                    grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[item_id].x, y:self.gridstackConfig[item_id].y, w:self.gridstackConfig[item_id].w, h:self.gridstackConfig[item_id].h, autoPosition:false, minW:3, maxW:null, minH:3, maxH:null, id:item_id});
                }
            } else {
                grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:5, h:4, autoPosition:true, minW:4, maxW:null, minH:3, maxH:null, id:item_id});
            }
        },

        renderListViewData: function(item) {
            var self = this;
            var list_view_data = JSON.parse(item.ks_list_view_data);
            var item_id = item.id,
                data_rows = list_view_data.data_rows,
                item_title = item.name;
            if (item.ks_list_view_type === "ungrouped" && list_view_data) {
                if (list_view_data.date_index) {
                    var index_data = list_view_data.date_index;
                    for (var i = 0; i < index_data.length; i++) {
                        for (var j = 0; j < list_view_data.data_rows.length; j++) {
                            var index = index_data[i]
                            var date = list_view_data.data_rows[j]["data"][index]
                            if (date) {
                                if (list_view_data.fields_type[index] === 'date'){
                                    list_view_data.data_rows[j]["data"][index] = moment(new Date(date)).format(this.date_format) , {}, {timezone: false};
                                }else{
                                    list_view_data.data_rows[j]["data"][index] = moment(new Date(date+" UTC")).format(this.datetime_format), {}, {timezone: false};
                                }
                            }else{
                                list_view_data.data_rows[j]["data"][index] = "";
                            }
                        }
                    }
                }
            }
            if (list_view_data) {
                for (var i = 0; i < list_view_data.data_rows.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
                        if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
                            if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
                                list_view_data.data_rows[i].data[j] = field_utils.format.float(list_view_data.data_rows[i].data[j], Float64Array, {digits:[0,item.ks_precision_digits]})
                            }
                        } else {
                            list_view_data.data_rows[i].data[j] = "";
                        }
                    }
                }
            }
            var $ksItemContainer = $(QWeb.render('ks_list_view_table', {
                list_view_data: list_view_data,
                item_id: item_id,
                list_type: item.ks_list_view_type,
                isDrill: self.ks_dashboard_data.ks_item_data[item_id]['isDrill']
            }));
            self.list_container = $ksItemContainer;
            if (list_view_data){
                var $ksitemBody = self.ksListViewBody(list_view_data,item_id)
                self.list_container.find('.ks_table_body').append($ksitemBody)
            }
            if (item.ks_list_view_type === "ungrouped") {
                $ksItemContainer.find('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
            }

            if (!item.ks_show_records) {
                $ksItemContainer.find('#ks_item_info').hide();
            }
            return $ksItemContainer
        },

        ksListViewBody: function(list_view_data, item_id) {
            var self = this;
            var itemid = item_id
            var  ks_data_calculation_type = self.ks_dashboard_data.ks_item_data[item_id].ks_data_calculation_type;
            var list_view_type = self.ks_dashboard_data.ks_item_data[item_id].ks_list_view_type
            var $ksitemBody = $(QWeb.render('ks_list_view_tmpl', {
                        list_view_data: list_view_data,
                        item_id: itemid,
                        calculation_type: ks_data_calculation_type,
                        isDrill: self.ks_dashboard_data.ks_item_data[item_id]['isDrill'],
                        list_type: list_view_type,
                    }));
            return $ksitemBody;

        },

        ksSum: function(count_1, count_2, item_info, field, target_1, $kpi_preview, kpi_data) {
            var self = this;
            var count = count_1 + count_2;
            if (field.ks_multiplier_active){
                item_info['count'] = KsGlobalFunction._onKsGlobalFormatter(count* field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                item_info['count_tooltip'] = field_utils.format.float(count * field.ks_multiplier, Float64Array, {digits:[0,field.ks_precision_digits]});
            }else{

                item_info['count'] = KsGlobalFunction._onKsGlobalFormatter(count, field.ks_data_formatting, field.ks_precision_digits);
                item_info['count_tooltip'] = field_utils.format.float(parseFloat(count), Float64Array, {digits:[0,field.ks_precision_digits]});
            }
             if (field.ks_multiplier_active){
                count = count * field.ks_multiplier;
            }
            item_info['target_enable'] = field.ks_goal_enable;
            var ks_color = (target_1 - count) > 0 ? "red" : "green";
            item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
            item_info['ks_comparison'] = true;
            var target_deviation = (target_1 - count) > 0 ? Math.round(((target_1 - count) / target_1) * 100) : Math.round((Math.abs((target_1 - count)) / target_1) * 100);
            if (target_deviation !== Infinity) item_info.target_deviation = field_utils.format.integer(target_deviation) + "%";
            else {
                item_info.target_deviation = target_deviation;
                item_info.pre_arrow = false;
            }
            var target_progress_deviation = target_1 == 0 ? 0 : Math.round((count / target_1) * 100);
            item_info.target_progress_deviation = field_utils.format.integer(target_progress_deviation) + "%";
            $kpi_preview = $(QWeb.render("ks_kpi_template_2", item_info));
            $kpi_preview.find('.target_deviation').css({
                "color": ks_color
            });
            if (field.ks_target_view === "Progress Bar") {
                $kpi_preview.find('#ks_progressbar').val(target_progress_deviation)
            }

            return $kpi_preview;
        },

        ksPercentage: function(count_1, count_2, field, item_info, target_1, $kpi_preview, kpi_data) {

            if (field.ks_multiplier_active){
                count_1 = count_1 * field.ks_multiplier;
                count_2 = count_2 * field.ks_multiplier;
            }
            var count = parseInt((count_1 / count_2) * 100);
            if (field.ks_multiplier_active){
                count = count * field.ks_multiplier;
            }
            item_info['count'] = count ? field_utils.format.integer(count) + "%" : "0%";
            item_info['count_tooltip'] = count ? count + "%" : "0%";
            item_info.target_progress_deviation = item_info['count']
            target_1 = target_1 > 100 ? 100 : target_1;
            item_info.target = target_1 + "%";
            item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
            var ks_color = (target_1 - count) > 0 ? "red" : "green";
            item_info['target_enable'] = field.ks_goal_enable;
            item_info['ks_comparison'] = false;
            item_info.target_deviation = item_info.target > 100 ? 100 : item_info.target;
            $kpi_preview = $(QWeb.render("ks_kpi_template_2", item_info));
            $kpi_preview.find('.target_deviation').css({
                "color": ks_color
            });
            if (field.ks_target_view === "Progress Bar") {
                if (count) $kpi_preview.find('#ks_progressbar').val(count);
                else $kpi_preview.find('#ks_progressbar').val(0);
            }

            return $kpi_preview;
        },

        renderKpi: function(item, grid) {
            var self = this;
            var field = item;
            var ks_date_filter_selection = field.ks_date_filter_selection;
            if (field.ks_date_filter_selection === "l_none") ks_date_filter_selection = self.ks_dashboard_data.ks_date_filter_selection;
            var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
            var kpi_data = JSON.parse(field.ks_kpi_data);
            var count_1 = kpi_data[0] ? kpi_data[0].record_data: undefined;
            var count_2 = kpi_data[1] ? kpi_data[1].record_data : undefined;
            var target_1 = kpi_data[0].target;
            var target_view = field.ks_target_view,
                pre_view = field.ks_prev_view;
            var ks_rgba_background_color = self._ks_get_rgba_format(field.ks_background_color);
            var ks_rgba_button_color = self._ks_get_rgba_format(field.ks_button_color);
            var ks_rgba_font_color = self._ks_get_rgba_format(field.ks_font_color);
            if (field.ks_goal_enable) {
                var diffrence = 0.0
               if(field.ks_multiplier_active){
                    diffrence = (count_1 * field.ks_multiplier) - target_1
                }else{
                    diffrence = count_1 - target_1
                }
                var acheive = diffrence >= 0 ? true : false;
                diffrence = Math.abs(diffrence);
                var deviation = Math.round((diffrence / target_1) * 100)
                if (deviation !== Infinity) deviation = deviation ? field_utils.format.integer(deviation) + '%' : 0 + '%';
            }
            if (field.ks_previous_period && ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0) {
                var previous_period_data = kpi_data[0].previous_period;
                var pre_diffrence = (count_1 - previous_period_data);
                if (field.ks_multiplier_active){
                    var previous_period_data = kpi_data[0].previous_period * field.ks_multiplier;
                    var pre_diffrence = (count_1 * field.ks_multiplier   - previous_period_data);
                }
                var pre_acheive = pre_diffrence > 0 ? true : false;
                pre_diffrence = Math.abs(pre_diffrence);
                var pre_deviation = previous_period_data ? field_utils.format.integer(parseInt((pre_diffrence / previous_period_data) * 100)) + '%' : "100%"
            }
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
            item['ksIsDashboardManager'] = self.ks_dashboard_data.ks_dashboard_manager;

            item['ksIsUser'] = true;
            if (item.ks_tv_play){
                item['ksIsUser'] = false;
            }
            var ks_icon_url;
            if (field.ks_icon_select == "Custom") {
                if (field.ks_icon[0]) {
                    ks_icon_url = 'data:image/' + (self.file_type_magic_word[field.ks_icon[0]] || 'png') + ';base64,' + field.ks_icon;
                } else {
                    ks_icon_url = false;
                }
            }
//            parseInt(Math.round((count_1 / target_1) * 100)) ? field_utils.format.integer(Math.round((count_1 / target_1) * 100)) : "0"
            var target_progress_deviation = String(Math.round((count_1  / target_1) * 100));
             if(field.ks_multiplier_active){
                var target_progress_deviation = String(Math.round(((count_1 * field.ks_multiplier) / target_1) * 100));
             }
            var ks_rgba_icon_color = self._ks_get_rgba_format(field.ks_default_icon_color)
            var item_info = {
                item: item,
                id: field.id,
                count_1: KsGlobalFunction.ksNumFormatter(kpi_data[0]['record_data'], 1),
                count_1_tooltip: kpi_data[0]['record_data'],
                count_2: kpi_data[1] ? String(kpi_data[1]['record_data']) : false,
                name: field.name ? field.name : field.ks_model_id.data.display_name,
                target_progress_deviation:target_progress_deviation,
                icon_select: field.ks_icon_select,
                default_icon: field.ks_default_icon,
                icon_color: ks_rgba_icon_color,
                target_deviation: deviation,
                target_arrow: acheive ? 'up' : 'down',
                ks_enable_goal: field.ks_goal_enable,
                ks_previous_period: ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0 ? field.ks_previous_period : false,
                target: KsGlobalFunction.ksNumFormatter(target_1, 1),
                previous_period_data: previous_period_data,
                pre_deviation: pre_deviation,
                pre_arrow: pre_acheive ? 'up' : 'down',
                target_view: field.ks_target_view,
                pre_view: field.ks_prev_view,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                ks_icon_url: ks_icon_url,
                ks_rgba_button_color:ks_rgba_button_color,
                ks_info: ks_description,

            }

            if (item_info.target_deviation === Infinity) item_info.target_arrow = false;
            item_info.target_progress_deviation = parseInt(item_info.target_progress_deviation) ? field_utils.format.integer(parseInt(item_info.target_progress_deviation)) : "0"
            if (field.ks_multiplier_active){
                item_info['count_1'] = KsGlobalFunction._onKsGlobalFormatter(kpi_data[0]['record_data'] * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                item_info['count_1_tooltip'] = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
                item_info['count_1'] = KsGlobalFunction._onKsGlobalFormatter(kpi_data[0]['record_data'], field.ks_data_formatting, field.ks_precision_digits);
            }
            item_info['target'] = KsGlobalFunction._onKsGlobalFormatter(kpi_data[0].target, field.ks_data_formatting, field.ks_precision_digits);
            if (field.ks_unit){
            if (field.ks_multiplier_active){
            var ks_record_count = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
            var ks_record_count = kpi_data[0]['record_data']
            }
            var ks_selection = field.ks_unit_selection;
            if (ks_selection === 'monetary') {
            var ks_currency_id = field.ks_currency_id;
            var ks_data = KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            ks_data = KsGlobalFunction.ks_monetary(ks_data, ks_currency_id);
            item_info['count_1'] = ks_data;
            } else if (ks_selection === 'custom') {
            var ks_field = field.ks_chart_unit;
            item_info['count_1']= ks_field+" "+KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            }else {
            item_info['count_1']= KsGlobalFunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            }
            }
            var $kpi_preview;
            if (!kpi_data[1]) {
                if (field.ks_target_view === "Number" || !field.ks_goal_enable) {
                    $kpi_preview = $(QWeb.render("ks_kpi_template", item_info));
                } else if (field.ks_target_view === "Progress Bar" && field.ks_goal_enable) {
                    $kpi_preview = $(QWeb.render("ks_kpi_template_3", item_info));
                    $kpi_preview.find('#ks_progressbar').val(parseInt(item_info.target_progress_deviation));

                }

                if (field.ks_goal_enable) {
                    if (acheive) {
                        $kpi_preview.find(".target_deviation").css({
                            "color": "green",
                        });
                    } else {
                        $kpi_preview.find(".target_deviation").css({
                            "color": "red",
                        });
                    }
                }
                if (field.ks_previous_period && String(previous_period_data) && ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0) {
                    if (pre_acheive) {
                        $kpi_preview.find(".pre_deviation").css({
                            "color": "green",
                        });
                    } else {
                        $kpi_preview.find(".pre_deviation").css({
                            "color": "red",
                        });
                    }
                }
                if ($kpi_preview.find('.ks_target_previous').children().length !== 2) {
                    $kpi_preview.find('.ks_target_previous').addClass('justify-content-center');
                }
            } else {
                switch (field.ks_data_comparison) {
                    case "None":
                        if (field.ks_multiplier_active){
                            var count_tooltip = String(count_1 * field.ks_multiplier) + "/" + String(count_2 * field.ks_multiplier);
                            var count = String(KsGlobalFunction.ksNumFormatter(count_1 * field.ks_multiplier, 1)) + "/" + String(KsGlobalFunction.ksNumFormatter(count_2 * field.ks_multiplier, 1));
                            var data1 = KsGlobalFunction._onKsGlobalFormatter(count_1 * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                            var data2 = KsGlobalFunction._onKsGlobalFormatter(count_2 * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                            if (field.ks_unit){
                            var ks_selection = field.ks_unit_selection;
                            if (ks_selection === 'monetary') {
                            var ks_currency_id = field.ks_currency_id;
                            data1 = KsGlobalFunction.ks_monetary(data1, ks_currency_id);
                            data2 = KsGlobalFunction.ks_monetary(data2, ks_currency_id)
                            item_info['count'] = data1+"/"+data2;
                            } else if (ks_selection === 'custom') {
                            var ks_field = field.ks_chart_unit;
                            data1= ks_field+" "+data1
                            data2= ks_field+" "+data2
                            item_info['count']= data1+"/"+data2
                            }
                            }else {
                            item_info['count']=String(KsGlobalFunction._onKsGlobalFormatter(count_1*field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits)) + "/" + String(KsGlobalFunction._onKsGlobalFormatter(count_2*field.ks_multiplier, field.ks_data_format, field.ks_precision_digits));
                            }
                         }else{
                            var count_tooltip = String(count_1) + "/" + String(count_2);
                            var count = String(KsGlobalFunction.ksNumFormatter(count_1, 1)) + "/" + String(KsGlobalFunction.ksNumFormatter(count_2, 1));
                           var data1 = KsGlobalFunction._onKsGlobalFormatter(count_1 , field.ks_data_formatting, field.ks_precision_digits);
                            var data2 = KsGlobalFunction._onKsGlobalFormatter(count_2 , field.ks_data_formatting, field.ks_precision_digits);
                            if (field.ks_unit){
                            var ks_selection = field.ks_unit_selection;
                            if (ks_selection === 'monetary') {
                            var ks_currency_id = field.ks_currency_id;
                            data1 = KsGlobalFunction.ks_monetary(data1, ks_currency_id);
                            data2 = KsGlobalFunction.ks_monetary(data2, ks_currency_id)
                            item_info['count'] = data1+"/"+data2;
                            } else{
                            var ks_field = field.ks_chart_unit;
                            data1= ks_field+" "+data1
                            data2= ks_field+" "+data2
                            item_info['count']= data1+"/"+data2
                            }
                         }else {

                            item_info['count']=String(KsGlobalFunction._onKsGlobalFormatter(count_1, field.ks_data_formatting, field.ks_precision_digits)) + "/" + String(KsGlobalFunction._onKsGlobalFormatter(count_2, field.ks_data_formatting, field.ks_precision_digits));
                            }
                        }
                        item_info['count_tooltip'] = count_tooltip;

                        item_info['target_enable'] = false;
                        $kpi_preview = $(QWeb.render("ks_kpi_template_2", item_info));
                        break;
                    case "Sum":
                        $kpi_preview = self.ksSum(count_1, count_2, item_info, field, target_1, $kpi_preview, kpi_data);
                        break;
                    case "Percentage":
                        $kpi_preview = self.ksPercentage(count_1, count_2, field, item_info, target_1, $kpi_preview, kpi_data);
                        break;
                    case "Ratio":
                        var gcd = self.ks_get_gcd(Math.round(count_1), Math.round(count_2));
                        if (item.ks_data_formatting == 'exact'){
                            if (count_1 && count_2) {
                            item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                            item_info['count'] = field_utils.format.float(count_1 / gcd, Float64Array,{digits: [0, field.ks_precision_digits]}) + ":" + field_utils.format.float(count_2 / gcd, Float64Array, {digits: [0, field.ks_precision_digits]});
                            } else {
                            item_info['count_tooltip'] = count_1 + ":" + count_2;
                            item_info['count'] = count_1 + ":" + count_2
                                   }
                          }else{
                            if (count_1 && count_2) {
                            item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                            item_info['count'] = KsGlobalFunction.ksNumFormatter(count_1 / gcd, 1) + ":" + KsGlobalFunction.ksNumFormatter(count_2 / gcd, 1);
                            }else {
                            item_info['count_tooltip'] = (count_1) + ":" + count_2;
                            item_info['count'] = KsGlobalFunction.ksNumFormatter(count_1, 1) + ":" + KsGlobalFunction.ksNumFormatter(count_2, 1);
                                  }
                          }
                        item_info['target_enable'] = false;
                        $kpi_preview = $(QWeb.render("ks_kpi_template_2", item_info));
                        break;
                }
            }
//            $kpi_preview.find('.ks_dashboarditem_id').css({
//                "background-color": ks_rgba_background_color,
//                "color": ks_rgba_font_color,
//            });
            this.ks_kpi_preview_background_style($kpi_preview, ks_rgba_background_color, ks_rgba_font_color, field);
            if (field.ks_previous_period && String(previous_period_data) && ks_valid_date_selection.indexOf(ks_date_filter_selection) >= 0 &&
            (field.ks_goal_enable && field.ks_target_view === "Progress Bar")){
                  $kpi_preview.addClass('ks_previous_period')
            }
            return $kpi_preview

        },

        ks_kpi_preview_background_style: function($kpi_preview, ks_rgba_background_color, ks_rgba_font_color, field){
            $kpi_preview.find('.ks_dashboarditem_id').css({
                "background-color": ks_rgba_background_color,
                "color": ks_rgba_font_color,
            });
        },

        ks_get_gcd: function(a, b) {
            return (b == 0) ? a : this.ks_get_gcd(b, a % b);
        },

        _onKsInputChange: function(e) {
            this.ksNewDashboardName = e.target.value
        },

        onKsDuplicateItemClick: function(e) {
            var self = this;
            var ks_item_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).parent().attr('id');
            var dashboard_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select').val();
            var dashboard_name = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').text();
            this._rpc({
                model: 'ks_dashboard_ninja.item',
                method: 'copy',
                args: [parseInt(ks_item_id), {
                    'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
                }],
            }).then(function(result) {
                self.displayNotification({
                    title:_t("Item Duplicated"),
                    message:_t('Selected item is duplicated to ' + dashboard_name + ' .'),
                    type: 'success',
                });
                $.when(self.ks_fetch_data()).then(function () {
                    self.ks_fetch_items_data().then(function (){
                        self.ksRenderDashboard();
                    });
                });
            })
        },

        ksOnListItemInfoClick: function(e) {
            var self = this;
            var item_id = e.currentTarget.dataset.itemId;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var action = {
                name: _t(item_data.name),
                type: 'ir.actions.act_window',
                res_model: e.currentTarget.dataset.model,
                domain: item_data.ks_domain || [],
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
            }
            if (e.currentTarget.dataset.listViewType === "ungrouped") {
                action['view_mode'] = 'form';
                action['views'] = [
                    [false, 'form']
                ];
                action['res_id'] = parseInt(e.currentTarget.dataset.recordId);
            } else {
                if (e.currentTarget.dataset.listType === "date_type") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['domain'] = domain;
                } else if (e.currentTarget.dataset.listType === "relational_type") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['domain'] = domain;
                    action['context']['search_default_' + e.currentTarget.dataset.groupby] = parseInt(e.currentTarget.dataset.recordId);
                } else if (e.currentTarget.dataset.listType === "other") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['context']['search_default_' + e.currentTarget.dataset.groupby] = parseInt(e.currentTarget.dataset.recordId);
                    action['domain'] = domain;
                }
            }
            self.do_action(action, {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            });
        },

        onKsMoveItemClick: function(e) {
            var self = this;
            var ks_item_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).parent().attr('id');
            var dashboard_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select').val();
            var dashboard_name = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').text();
            this._rpc({
                model: 'ks_dashboard_ninja.item',
                method: 'write',
                args: [parseInt(ks_item_id), {
                    'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
                }],
            }).then(function(result) {
                self.displayNotification({
                    title:_t("Item Moved"),
                    message:_t('Selected item is moved to ' + dashboard_name + ' .'),
                    type: 'success',
                });
                $.when(self.ks_fetch_data()).then(function() {
                    $.when(self.ks_fetch_items_data()).then(function(){
                        self.ks_remove_update_interval();
                        self.ksRenderDashboard();
                        self.ks_set_update_interval();
                    });
                });
            });
        },

        _KsGetDateValues: function() {
            var self = this;

            //Setting Date Filter Selected Option in Date Filter DropDown Menu
            var date_filter_selected = self.ks_dashboard_data.ks_date_filter_selection;
            if (self.ksDateFilterSelection == 'l_none'){
                    date_filter_selected = self.ksDateFilterSelection;
//                    $('.ks_date_input_fields').addClass("ks_hide");
            }
            self.$el.find('#' + date_filter_selected).addClass("ks_date_filter_selected");
            self.$el.find('#ks_date_filter_selection').text(self.ks_date_filter_selections[date_filter_selected]);

            if (self.ks_dashboard_data.ks_date_filter_selection === 'l_custom') {
                self.$el.find('.ks_date_input_fields').removeClass("ks_hide");
                self.$el.find('.ks_date_filter_dropdown').addClass("ks_btn_first_child_radius");
            } else if (self.ks_dashboard_data.ks_date_filter_selection !== 'l_custom') {
                self.$el.find('.ks_date_input_fields').addClass("ks_hide");
            }
        },

        _onKsClearDateValues: function(ks_l_none=false) {
            var self = this;
            self.ksDateFilterSelection = 'l_none';
            self.ksDateFilterStartDate = false;
            self.ksDateFilterEndDate = false;

            self.ks_fetch_items_data().then(function () {
//                self.ksRenderDashboard();
                $('.ks_date_input_fields').addClass("ks_hide");
                $('.ks_date_filter_dropdown').removeClass("ks_btn_first_child_radius");

                  var res = {};
                    for (const [key, value] of Object.entries(self.ks_dashboard_data.ks_item_data)) {
                        if (value.ks_dashboard_item_type != "ks_to_do") {
                            res[key] = value;
                        }
                    }
                  self.ksUpdateDashboardItem(Object.keys(res))
           });
           var context = {
                ksDateFilterSelection: self.ksDateFilterSelection,
                ksDateFilterStartDate: self.ksDateFilterStartDate,
                ksDateFilterEndDate: self.ksDateFilterEndDate,
           }
           self.state['user_context']=context

        },


        _renderDateFilterDatePicker: function() {
            var self = this;
            self.$el.find(".ks_dashboard_link").removeClass("ks_hide");
            var startDate = self.ks_dashboard_data.ks_dashboard_start_date ? moment.utc(self.ks_dashboard_data.ks_dashboard_start_date).local() : moment();
            var endDate = self.ks_dashboard_data.ks_dashboard_end_date ? moment.utc(self.ks_dashboard_data.ks_dashboard_end_date).local() : moment();

            this.ksStartDatePickerWidget = new(datepicker.DateTimeWidget)(this);

            this.ksStartDatePickerWidget.appendTo(self.$el.find(".ks_date_input_fields")).then((function() {
                this.ksStartDatePickerWidget.$el.addClass("ks_btn_middle_child o_input");
                this.ksStartDatePickerWidget.$el.find("input").attr("placeholder", "Start Date");
                this.ksStartDatePickerWidget.setValue(startDate);
                this.ksStartDatePickerWidget.on("datetime_changed", this, function() {
                    self.$el.find(".apply-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find(".clear-dashboard-date-filter").removeClass("ks_hide");
                });
            }).bind(this));

            this.ksEndDatePickerWidget = new(datepicker.DateTimeWidget)(this);
            this.ksEndDatePickerWidget.appendTo(self.$el.find(".ks_date_input_fields")).then((function() {
                this.ksEndDatePickerWidget.$el.addClass("ks_btn_last_child o_input");
                this.ksStartDatePickerWidget.$el.find("input").attr("placeholder", "Start Date");
                this.ksEndDatePickerWidget.setValue(endDate);
                this.ksEndDatePickerWidget.on("datetime_changed", this, function() {
                    self.$el.find(".apply-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find(".clear-dashboard-date-filter").removeClass("ks_hide");
                });
            }).bind(this));

            self._KsGetDateValues();
        },

        _onKsApplyDateFilter: function(e) {
            var self = this;
            var start_date = self.ksStartDatePickerWidget.$input.val();
            var end_date = self.ksEndDatePickerWidget.$input.val();
            $('.ks_dashboard_item_drill_up').addClass("d-none")
            if (start_date === "Invalid date") {
                alert("Invalid Date is given in Start Date.")
            } else if (end_date === "Invalid date") {
                alert("Invalid Date is given in End Date.")
            } else if (self.$el.find('.ks_date_filter_selected').attr('id') !== "l_custom") {

                self.ksDateFilterSelection = self.$el.find('.ks_date_filter_selected').attr('id');
                var res = {};
                for (const [key, value] of Object.entries(self.ks_dashboard_data.ks_item_data)) {
                    if (value.ks_dashboard_item_type != "ks_to_do") {
                        res[key] = value;
                    }
                }
                var context = {
                    ksDateFilterSelection: self.ksDateFilterSelection,
                    ksDateFilterStartDate: self.ksDateFilterStartDate,
                    ksDateFilterEndDate: self.ksDateFilterEndDate,
                }
                self.state['user_context']=context
                self.ks_fetch_items_data().then(function(result){
                    self.ksUpdateDashboardItem(Object.keys(res));
                    self.$el.find(".apply-dashboard-date-filter").addClass("ks_hide");
                    self.$el.find(".clear-dashboard-date-filter").addClass("ks_hide");

                });
            } else {
                if (start_date && end_date) {
                    if (moment(start_date, self.datetime_format) <= moment(end_date, self.datetime_format)) {
                        var start_date = new moment(start_date, self.datetime_format).format("YYYY-MM-DD H:m:s");
                        var end_date = new moment(end_date, self.datetime_format).format("YYYY-MM-DD H:m:s");
                        if (start_date === "Invalid date" || end_date === "Invalid date"){
                            alert(_t("Invalid Date"));
                        }else{
                            self.ksDateFilterSelection = self.$el.find('.ks_date_filter_selected').attr('id');
                            self.ksDateFilterStartDate = start_date;
                            self.ksDateFilterEndDate = end_date;

                            self.ks_fetch_items_data().then(function(result){
                                var res = {};
                                for (const [key, value] of Object.entries(self.ks_dashboard_data.ks_item_data)) {
                                    if (value.ks_dashboard_item_type != "ks_to_do") {
                                        res[key] = value;
                                    }
                                }
                            var context = {
                                ksDateFilterSelection: self.ksDateFilterSelection,
                                ksDateFilterStartDate: self.ksDateFilterStartDate,
                                ksDateFilterEndDate: self.ksDateFilterEndDate,
                            }
                            self.state['user_context']=context
                                self.ksUpdateDashboardItem(Object.keys(res));
                                self.$el.find(".apply-dashboard-date-filter").addClass("ks_hide");
                                self.$el.find(".clear-dashboard-date-filter").addClass("ks_hide");
                            });

                       }

                    } else {
                        alert(_t("Start date should be less than end date"));
                    }
                } else {
                    alert(_t("Please enter start date and end date"));
                }
            }
        },

        _ksOnDateFilterMenuSelect: function(e) {
            if (e.target.id !== 'ks_date_selector_container') {
                var self = this;
                _.each($('.ks_date_filter_selected'), function($filter_options) {
                    $($filter_options).removeClass("ks_date_filter_selected")
                });
                $(e.target.parentElement).addClass("ks_date_filter_selected");
                $('#ks_date_filter_selection').text(self.ks_date_filter_selections[e.target.parentElement.id]);

                if (e.target.parentElement.id !== "l_custom") {
                    e.target.parentElement.id === "l_none" ?  self._onKsClearDateValues(true) : self._onKsApplyDateFilter();
                    $('.ks_date_input_fields').addClass("ks_hide");
                    $('.ks_date_filter_dropdown').removeClass("ks_btn_first_child_radius");

                } else if (e.target.parentElement.id === "l_custom") {
                    $("#ks_start_date_picker").val(null).removeClass("ks_hide");
                    $("#ks_end_date_picker").val(null).removeClass("ks_hide");
                    $('.ks_date_input_fields').removeClass("ks_hide");
                    $('.ks_date_filter_dropdown').addClass("ks_btn_first_child_radius");
                    self.$el.find(".apply-dashboard-date-filter").removeClass("ks_hide");
                    self.$el.find(".clear-dashboard-date-filter").removeClass("ks_hide");
                }
            }
        },

        ksChartExportXlsCsv: function(e) {
            var chart_id = e.currentTarget.dataset.chartId;
            var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
            var context = this.getContext();
            if (this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type === 'ks_list_view'){
             var params = this.ksGetParamsForItemFetch(parseInt(chart_id));
            var data = {
                "header": name,
                "chart_data": this.ks_dashboard_data.ks_item_data[chart_id].ks_list_view_data,
                "ks_item_id": chart_id,
                "ks_export_boolean": true,
                "context": context,
                'params':params,
            }
            }else{
                var data = {
                    "header": name,
                    "chart_data": this.ks_dashboard_data.ks_item_data[chart_id].ks_chart_data,
            }
            }

            framework.blockUI();
            this.getSession().get_file({
                url: '/ks_dashboard_ninja/export/' + e.currentTarget.dataset.format,
                data: {
                    data: JSON.stringify(data)
                },
                complete: framework.unblockUI,
                error: (error) => this.call('crash_manager', 'rpc_error', error),
            });
        },

        ksChartExportPdf : function(e){
            var self = this;
            var chart_id = e.currentTarget.dataset.chartId;
            var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
            var base64_image
            if(this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_bullet_chart" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_funnel_chart" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_flower_view" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_radialBar_chart" || this.ks_dashboard_data.ks_item_data[chart_id].ks_dashboard_item_type == "ks_map_view"){
                base64_image = (this.chart_container[chart_id].root.dom).querySelector("canvas").toDataURL("image/png")
            }else{
                base64_image = this.chart_container[chart_id].toBase64Image();
            }
            var $ks_el = $($(self.$el.find(".grid-stack-item[gs-id=" + chart_id + "]")).find('.ks_chart_card_body'));
            var ks_height = $ks_el.height()
            var ks_image_def = {
                content: [{
                        image: base64_image,
                        width: 500,
                        height: ks_height,
                        }],
                images: {
                    bee: base64_image
                }
            };
            pdfMake.createPdf(ks_image_def).download(name + '.pdf');
        },

        ksItemExportJson: function(e) {
            var itemId = $(e.target).parents('.ks_dashboard_item_button_container')[0].dataset.item_id;
            var name = this.ks_dashboard_data.ks_item_data[itemId].name;
            var data = {
                'header': name,
                item_id: itemId,
            }
            framework.blockUI();
            this.getSession().get_file({
                url: '/ks_dashboard_ninja/export/item_json',
                data: {
                    data: JSON.stringify(data)
                },
                complete: framework.unblockUI,
                error: (error) => this.call('crash_manager', 'rpc_error', error),
            });
            e.stopPropagation();
        },

        //List View pagination records
        ksLoadMoreRecords: function(e) {
            var self = this;
            var ks_intial_count = e.target.parentElement.dataset.prevOffset;
            var ks_offset = e.target.parentElement.dataset.next_offset;
            var itemId = e.currentTarget.dataset.itemId;
            var offset = self.ks_dashboard_data.ks_item_data[itemId].ks_pagination_limit;

            if (itemId in self.ksUpdateDashboard) {
                clearInterval(self.ksUpdateDashboard[itemId])
                delete self.ksUpdateDashboard[itemId];
            }
            var params = self.ksGetParamsForItemFetch(parseInt(itemId));
            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_get_list_view_data_offset',
                context: self.getContext(),
                args: [parseInt(itemId), {
                    ks_intial_count: ks_intial_count,
                    offset: ks_offset,
                    }, parseInt(self.ks_dashboard_id), params],
            }).then(function(result) {
                var item_data = self.ks_dashboard_data.ks_item_data[itemId];
                self.ks_dashboard_data.ks_item_data[itemId]['ks_list_view_data'] = result.ks_list_view_data;
                var item_view = self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]");
                item_view.find('.card-body').empty();
                item_view.find('.card-body').append(self.renderListViewData(item_data));
                $(e.currentTarget).parents('.ks_pager').find('.ks_value').text(result.offset + "-" + result.next_offset);
                e.target.parentElement.dataset.next_offset = result.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset;
                $(e.currentTarget.parentElement).find('.ks_load_previous').removeClass('ks_event_offer_list');
                if (result.next_offset < parseInt(result.offset) + (offset - 1) || result.next_offset == item_data.ks_record_count || result.next_offset === result.limit){
                    $(e.currentTarget).addClass('ks_event_offer_list');
                }
            });
        },

        ksLoadPreviousRecords: function(e) {
            var self = this;
            var itemId = e.currentTarget.dataset.itemId;
            var offset = self.ks_dashboard_data.ks_item_data[itemId].ks_pagination_limit;
            var ks_offset =  parseInt(e.target.parentElement.dataset.prevOffset) - (offset + 1) ;
            var ks_intial_count = e.target.parentElement.dataset.next_offset;
            if (ks_offset <= 0) {
                var updateValue = self.ks_dashboard_data.ks_set_interval;
                if (updateValue) {
                    var updateinterval = setInterval(function() {
                        self.ksFetchUpdateItem(itemId)
                    }, updateValue);
                    self.ksUpdateDashboard[itemId] = updateinterval;
                }
            }
            var params = self.ksGetParamsForItemFetch(parseInt(itemId));
            this._rpc({
                model: 'ks_dashboard_ninja.board',
                method: 'ks_get_list_view_data_offset',
                context: self.getContext(),
                args: [parseInt(itemId), {
                    ks_intial_count: ks_intial_count,
                    offset: ks_offset,
                    }, parseInt(self.ks_dashboard_id), params],
            }).then(function(result) {
                var item_data = self.ks_dashboard_data.ks_item_data[itemId];
                self.ks_dashboard_data.ks_item_data[itemId]['ks_list_view_data'] = result.ks_list_view_data;
                var item_view = self.$el.find(".grid-stack-item[gs-id=" + item_data.id + "]");
                item_view.find('.card-body').empty();
                item_view.find('.card-body').append(self.renderListViewData(item_data));
                $(e.currentTarget).parents('.ks_pager').find('.ks_value').text(result.offset + "-" + result.next_offset);
                e.target.parentElement.dataset.next_offset = result.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset;
                $(e.currentTarget.parentElement).find('.ks_load_next').removeClass('ks_event_offer_list');
                if (result.offset === 1) {
                    $(e.currentTarget).addClass('ks_event_offer_list');
                }
            });
        },
         createaidash: function(ev){
           var self= this;
           var action = {
                name: _t('Generate items with AI'),
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.arti_int',
                domain: [],
                context: {
                'ks_dashboard_id':this.ks_dashboard_id
                },
                views: [
                    [false, 'form']
                ],
                view_mode: 'form',
                target: 'new',
           }
           self.do_action(action)

        },
        createaidashboard: function(ev){
          var self= this;
           var action = {
                name: _t('Generate Dashboard with AI'),
                type: 'ir.actions.act_window',
                res_model: 'ks_dashboard_ninja.ai_dashboard',
                domain: [],
                context: {
                'ks_dashboard_id':this.ks_dashboard_id
                },
                views: [
                    [false, 'form']
                ],
                view_mode: 'form',
                target: 'new',
           }
           self.do_action(action)
        }

    });

    core.action_registry.add('ks_dashboard_ninja', KsDashboardNinja);

    patch(WebClient.prototype, 'ks_dn.WebClient', {
        async loadRouterState(...args) {
            var self = this;
            const sup = await this._super(...args);
            const ks_reload_menu = async (id) =>  {
                this.menuService.reload().then(() => {
                      self.menuService.selectMenu(id);
                  });
            }
            this.actionService.ksDnReloadMenu = ks_reload_menu;
            return sup;
        }

    });

    return KsDashboardNinja;
});