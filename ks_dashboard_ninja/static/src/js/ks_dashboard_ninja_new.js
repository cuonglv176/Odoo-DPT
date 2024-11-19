/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState ,onMounted, onWillRender, useRef, onWillPatch, onRendered, useEffect, onWillUpdateProps  } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { localization } from "@web/core/l10n/localization";
import { session } from "@web/session";
import { download } from "@web/core/network/download";
import { BlockUI } from "@web/core/ui/block_ui";
import { WebClient } from "@web/webclient/webclient";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { isBrowserChrome, isMobileOS } from "@web/core/browser/feature_detection";
import { loadBundle } from '@web/core/assets';
import {FormViewDialog} from '@web/views/view_dialogs/form_view_dialog';
import { renderToElement } from "@web/core/utils/render";
import {globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions'
import { Ksdashboardtile } from '@ks_dashboard_ninja/components/ks_dashboard_tile_view/ks_dashboard_tile';
import { Ksdashboardlistview } from '@ks_dashboard_ninja/components/ks_dashboard_list_view/ks_dashboard_list';
import { Ksdashboardtodo } from '@ks_dashboard_ninja/components/ks_dashboard_to_do_item/ks_dashboard_to_do';
import { Ksdashboardkpiview } from '@ks_dashboard_ninja/components/ks_dashboard_kpi_view/ks_dashboard_kpi';
import { Ksdashboardgraph } from '@ks_dashboard_ninja/components/ks_dashboard_graphs/ks_dashboard_graphs';
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
const { DateTime } = luxon;
import {formatDate,formatDateTime} from "@web/core/l10n/dates";
import {parseDateTime,parseDate,} from "@web/core/l10n/dates";


export class KsDashboardNinja extends Component {

    setup() {
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
        this._rpc = useService("rpc");
        this.dialogService = useService("dialog");
        this.header =  useRef("ks_dashboard_header");
        this.main_body = useRef("ks_main_body");
        this.reload_menu_option = {
            reload:this.props.action.context.ks_reload_menu,
            menu_id: this.props.action.context.ks_menu_id
        };
        this.ks_mode = 'active';
        this.action_manager = parent;
//      this.controllerID = params.controllerID;
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

        this.date_format = localization.dateFormat
        //        this.date_format = this.date_format.replace(/\bYY\b/g, "YYYY");
        this.datetime_format = localization.dateTimeFormat
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

        this.ks_dashboard_id = this.props.action.params.ks_dashboard_id;

        this.gridstack_options = {
            staticGrid:true,
            float: false,
            cellHeight: 80,
            styleInHead : true,
//          disableOneColumnMode: true,
        };
        if (isMobileOS()) {
            this.gridstack_options.disableOneColumnMode = false
        }
        this.gridstackConfig = {};
        this.grid = true;
        this.chartMeasure = {};
        this.chart_container = {};
        this.list_container = {};
        this.state = useState({
            ks_dashboard_name: '',
            ks_multi_layout: false,
            ks_dash_name: '',
            ks_dashboard_manager :false,
            date_selection_data: {},
            date_selection_order :[],
            ks_show_create_layout_option : true,
            ks_show_layout :false,
            ks_selected_board_id:false,
            ks_child_boards:false,
            ks_dashboard_data:{},
            ks_dn_pre_defined_filters:[],
            ks_dashboard_item_length:0,
            ks_dashboard_items:[],
            update:false,
            ksDateFilterSelection :false,
            pre_defined_filter :{},
            ksDateFilterStartDate: DateTime.now(),
            ksDateFilterEndDate:DateTime.now()
        })
        this.ksChartColorOptions = ['default', 'cool', 'warm', 'neon'];
        this.ksDateFilterSelection = false;
        this.ksDateFilterStartDate = false;
        this.ksDateFilterEndDate = false;
        this.ksUpdateDashboard = {};
        $("head").append('<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">');
        if(this.props.action.context.ks_reload_menu){
            this.trigger_up('reload_menu_data', { keep_open: true, scroll_to_bottom: true});
        }
        var context = {
            ksDateFilterSelection: this.ksDateFilterSelection,
            ksDateFilterStartDate: self.ksDateFilterStartDate,
            ksDateFilterEndDate: self.ksDateFilterEndDate,
        }
        this.dn_state = {}
        this.dn_state['user_context']=context
        onWillStart(this.willStart);
        onWillRender(this.dashboard_mount);
        onMounted(() => this.grid_initiate());
    }


    willStart(){
        var self = this;
        var def;
        if (this.reload_menu_option.reload && this.reload_menu_option.menu_id) {
            def = this.getParent().actionService.ksDnReloadMenu(this.reload_menu_option.menu_id);
        }
        return $.when(def, loadBundle("ks_dashboard_ninja.ks_dashboard_lib")).then(function() {
            return self.ks_fetch_data().then(function(){
                return self.ks_fetch_items_data()
            });
        });
    }

    grid_initiate(){
        var self=this;
        var $gridstackContainer = $(".grid-stack");
        if($gridstackContainer.length){
            this.grid = GridStack.init(this.gridstack_options,$gridstackContainer[0]);
            var item = self.ksSortItems(self.ks_dashboard_data.ks_item_data)
            if(this.ks_dashboard_data.ks_gridstack_config){
                this.gridstackConfig = JSON.parse(this.ks_dashboard_data.ks_gridstack_config);
            }
            for (var i = 0; i < item.length; i++) {
                var graphs = ['ks_scatter_chart','ks_bar_chart', 'ks_horizontalBar_chart', 'ks_line_chart', 'ks_area_chart', 'ks_doughnut_chart','ks_polarArea_chart','ks_pie_chart','ks_flower_view', 'ks_radar_view','ks_radialBar_chart','ks_map_view','ks_funnel_chart','ks_bullet_chart', 'ks_to_do', 'ks_list_view']
                var $ks_preview = $('#' + item[i].id)
                if ($ks_preview.length) {
                    if (item[i].id in self.gridstackConfig) {
                         self.grid.addWidget($ks_preview[0], {x:self.gridstackConfig[item[i].id].x, y:self.gridstackConfig[item[i].id].y, w:self.gridstackConfig[item[i].id].w, h: self.gridstackConfig[item[i].id].h, autoPosition:true, minW:2, maxW:null, minH:2, maxH:null, id:item[i].id});
                    } else if ( graphs.includes (item[i].ks_dashboard_item_type)) {
                         self.grid.addWidget($ks_preview[0], {x:0, y:0, w:5, h:5,autoPosition:true,minW:4,maxW:null,minH:3,maxH:null, id :item[i].id});
                    }else{
                        self.grid.addWidget($ks_preview[0], {x:0, y:0, w:3, h:2,autoPosition:true,minW:2,maxW:null,minH:2,maxH:2,id:item[i].id});
                    }
                }
            }
            this.grid.setStatic(true);
        }
        // Events //
        const ks_element = this.main_body.el;
        Object.values(ks_element.querySelectorAll(".ks_duplicate_item")).map((item) => { item.addEventListener('click', this.onKsDuplicateItemClick.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_move_item")).map((item) => { item.addEventListener('click', this.onKsMoveItemClick.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_dashboard_item_delete")).map((item) => { item.addEventListener('click', this._onKsDeleteItemClick.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_chart_xls_csv_export")).map((item) => { item.addEventListener('click', this.ksChartExportXlsCsv.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_chart_pdf_export")).map((item) => { item.addEventListener('click', this.ksChartExportPdf.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_chart_image_export")).map((item) => { item.addEventListener('click', this.ksChartExportimage.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_chart_json_export")).map((item) => { item.addEventListener('click', this.ksItemExportJson.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_dashboard_quick_edit_action_popup")).map((item) => { item.addEventListener('click', this.onEditItemTypeClick.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_dashboard_menu_container")).map((item) => { item.addEventListener('click', this.stoppropagation.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_item_description")).map((item) => { item.addEventListener('click', this.stoppropagation.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_item_click")).map((item) => { item.addEventListener('click', this._onKsItemClick.bind(this))})
        Object.values(ks_element.querySelectorAll(".ks_dashboard_item_action")).map((item) => { item.addEventListener('click', this.ks_dashboard_item_action.bind(this))})
        this.ksRenderDashboard();
    }

    getContext() {
        var self = this;
        var context = {
            ksDateFilterSelection: self.ksDateFilterSelection,
            ksDateFilterStartDate: self.ksDateFilterStartDate,
            ksDateFilterEndDate: self.ksDateFilterEndDate,
        }
        if(self.dn_state['user_context']['ksDateFilterSelection'] !== undefined && self.ksDateFilterSelection !== 'l_none'){
            context = self.dn_state['user_context']
        }
        return Object.assign(context, session.user_context);
    }

    ks_fetch_data(){
        var self = this;
        return jsonrpc("/web/dataset/call_kw",{
            model: 'ks_dashboard_ninja.board',
            method: 'ks_fetch_dashboard_data',
            args: [self.ks_dashboard_id],
            kwargs : {context:self.getContext()},
//            context: self.getContext()
        }).then(function(result) {
        //                result = self.normalize_dn_data(result);
            self.ks_dashboard_data = result;
            self.ks_dashboard_data['ks_dashboard_id'] = self.props.action.params.ks_dashboard_id
            self.ks_dashboard_data['context'] = self.getContext()
            self.ks_dashboard_data['ks_ai_dashboard'] = false
            if(self.dn_state['domain_data'] != undefined){
                self.ks_dashboard_data.ks_dashboard_domain_data=self.dn_state['domain_data']
                Object.values(self.ks_dashboard_data.ks_dashboard_pre_domain_filter).map((x)=>{
                    if(self.dn_state['domain_data'][x['model']] != undefined){
                        if(self.dn_state['domain_data'][x['model']]['ks_domain_index_data'][0]['label'].indexOf(x['name']) ==-1){
                            self.ks_dashboard_data.ks_dashboard_pre_domain_filter[x['id']].active = false;
                        }
                    }
                    else{
                        self.ks_dashboard_data.ks_dashboard_pre_domain_filter[x['id']].active = false;
                    }
                })
            }
        });
    }

    dashboard_mount(){
        var self = this;
//        var items = self.ksSortItems(self.ks_dashboard_data.ks_item_data)
        var items = Object.values(self.ks_dashboard_data.ks_item_data)
        self.state.ks_dashboard_items = items
        self.ks_dashboard_data['context'] = self.getContext()

    }

    ks_fetch_items_data(){
        var self = this;
        var items_promises = []

        self.ks_dashboard_data.ks_dashboard_items_ids.forEach(function(item_id){
            items_promises.push(jsonrpc("/web/dataset/call_kw",{
                model: "ks_dashboard_ninja.board",
                method: "ks_fetch_item",
                args : [[item_id], self.ks_dashboard_id, self.ksGetParamsForItemFetch(item_id)],
                kwargs:{context:self.getContext()}
            }).then(function(result){
                self.ks_dashboard_data.ks_item_data[item_id] = result[item_id];
                self.state.ks_show_create_layout_option = (Object.keys(self.ks_dashboard_data.ks_item_data).length > 0) && self.ks_dashboard_data.ks_dashboard_manager
            }));
        });
        self.state.ks_dashboard_name = self.ks_dashboard_data.name,
        self.state.ks_multi_layout = self.ks_dashboard_data.multi_layouts,
        self.state.ks_dash_name = self.ks_dashboard_data.name,
        self.state.ks_dashboard_manager = self.ks_dashboard_data.ks_dashboard_manager,
        self.state.date_selection_data = self.ks_date_filter_selections,
        self.state.date_selection_order = self.ks_date_filter_selection_order,
        self.state.ks_show_layout = self.ks_dashboard_data.ks_dashboard_manager && self.ks_dashboard_data.ks_child_boards && true,
        self.state.ks_selected_board_id = self.ks_dashboard_data.ks_selected_board_id,
        self.state.ks_child_boards = self.ks_dashboard_data.ks_child_boards,
        self.state.ks_dashboard_data = self.ks_dashboard_data,
        self.state.ks_dn_pre_defined_filters = Object.values(self.ks_dashboard_data.ks_dashboard_pre_domain_filter).sort(function(a, b){return a.sequence - b.sequence}),
        self.state.ks_dashboard_item_length = self.ks_dashboard_data.ks_dashboard_items_ids.length
        self.state.update = false
        self.state.ksDateFilterSelection = self.state.ksDateFilterSelection == false ? 'none' : self.state.ksDateFilterSelection,
        self.state.pre_defined_filter = {}
        self.state.ksDateFilterStartDate = DateTime.now()
        self.state.ksDateFilterEndDate = DateTime.now()
        self.state.ks_user_name = session.name
        return Promise.all(items_promises)

    }


    ksGetParamsForItemFetch(){
        return {};
    }

    ksRenderDashboard(){
        var self = this;
        if (self.ks_dashboard_data.ks_child_boards) self.ks_dashboard_data.name = this.ks_dashboard_data.ks_child_boards[self.ks_dashboard_data.ks_selected_board_id][0];
        if (!isMobileOS()) {
            $(self.header.el).addClass("ks_dashboard_header_sticky")
        }
        if (Object.keys(self.ks_dashboard_data.ks_item_data).length===0){
            $(self.header.el).find('.ks_dashboard_link').addClass("d-none");
            $(self.header.el).find('.ks_dashboard_edit_layout').addClass("d-none");
        }
        if(!self.state.ks_dashboard_manager){
            $(self.header.el).find('#ks_dashboard_title').addClass("ks_user")
        }
      self.ksRenderDashboardMainContent();
    }

    ksRenderDashboardMainContent(){
        var self = this;
        if (isMobileOS() && $('#ks_dn_layout_button :first-child').length > 0) {
            $('.ks_am_element').append($('#ks_dn_layout_button :first-child')[0].innerText);
            $(self.header.el).find("#ks_dn_layout_button").addClass("ks_hide");
        }
        if (Object.keys(self.ks_dashboard_data.ks_item_data).length){
        // todo  implement below mentioned function
            self._renderDateFilterDatePicker();
            $(self.header.el).find('.ks_dashboard_link').removeClass("ks_hide");
        } else if (!Object.keys(self.ks_dashboard_data.ks_item_data).length) {
            $(self.header.el).find('.ks_dashboard_link').addClass("ks_hide");
        }
    }

    _renderDateFilterDatePicker() {
        var self = this;
        $(self.header.el).find(".ks_dashboard_link").removeClass("ks_hide");
        self._KsGetDateValues();
    }

    get current_date(){
        return DateTime.now()
    }

    loadDashboardData(date = false){
        var self = this;
        $(self.header.el).find(".apply-dashboard-date-filter").removeClass("ks_hide");
        $(self.header.el).find(".clear-dashboard-date-filter").removeClass("ks_hide");
    }

    _KsGetDateValues() {
            var self = this;
            //Setting Date Filter Selected Option in Date Filter DropDown Menu
            var date_filter_selected = self.ks_dashboard_data.ks_date_filter_selection;
            if (self.ksDateFilterSelection == 'l_none'){
                    var date_filter_selected = self.ksDateFilterSelection;
            }
            $(self.header.el).find('#' + date_filter_selected).addClass("ks_date_filter_selected");
            $(self.header.el).find('#ks_date_filter_selection').text(self.ks_date_filter_selections[date_filter_selected]);

            if (self.ks_dashboard_data.ks_date_filter_selection === 'l_custom') {
                var ks_end_date = self.ks_dashboard_data.ks_dashboard_end_date;
                var ks_start_date = self.ks_dashboard_data.ks_dashboard_start_date;

                $(self.header.el).find(".ks_wdn_start_date_picker").val(moment.utc(ks_start_date).local().format(self.datetime_format));
                $(self.header.el).find(".ks_wdn_end_date_picker").val(moment.utc(ks_end_date).local().format(self.datetime_format));
                $(self.header.el).find('.ks_date_input_fields').removeClass("ks_hide");
                $(self.header.el).find('.ks_date_filter_dropdown').addClass("ks_btn_first_child_radius");
            } else if (self.ks_dashboard_data.ks_date_filter_selection !== 'l_custom') {
                $(self.header.el).find('.ks_date_input_fields').addClass("ks_hide");
            }
        }

    _ksOnDateFilterMenuSelect(e) {
        if (e.target.id !== 'ks_date_selector_container') {
            var self = this;
            $.each($('.ks_date_filter_selected'), function(idx, $itm) {
                $($itm).removeClass("ks_date_filter_selected")
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
                $(self.header.el).find(".apply-dashboard-date-filter").removeClass("ks_hide");
                $(self.header.el).find(".clear-dashboard-date-filter").removeClass("ks_hide");
            }
        }
    }

    _onKsApplyDateFilter(e) {
        var self = this;
        var start_date = $('#ks_btn_middle_child').val();
        var end_date = $('#ks_btn_last_child').val();
        $('.ks_dashboard_item_drill_up').addClass("d-none")
        if (start_date === "Invalid date") {
            alert("Invalid Date is given in Start Date.")
        } else if (end_date === "Invalid date") {
            alert("Invalid Date is given in End Date.")
        } else if ($(self.header.el).find('.ks_date_filter_selected').attr('id') !== "l_custom") {
            self.ksDateFilterSelection = $(self.header.el).find('.ks_date_filter_selected').attr('id');
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
            self.dn_state['user_context']=context
                $(self.header.el).find(".apply-dashboard-date-filter").addClass("ks_hide");
                $(self.header.el).find(".clear-dashboard-date-filter").addClass("ks_hide");
                self.state.ksDateFilterSelection = $(self.header.el).find('.ks_date_filter_selected').attr('id');
                self.state.pre_defined_filter = {}
        } else {
            if (start_date && end_date) {
                if (parseDateTime(start_date, self.datetime_format) <= parseDateTime(end_date, self.datetime_format)) {
//                    var start_date = parseDateTime(start_date, self.datetime_format).format("YYYY-MM-DD H:m:s");
                    var start_date = formatDateTime(parseDateTime(start_date, self.datetime_format), { format: "yyyy-MM-dd HH:mm:ss"})
                    var end_date = formatDateTime(parseDateTime(end_date, self.datetime_format), { format: "yyyy-MM-dd HH:mm:ss" })
//                    var end_date = formatDateTime(end_date, self.datetime_format).format("YYYY-MM-DD H:m:s");
                    if (start_date === "Invalid date" || end_date === "Invalid date"){
                        alert(_t("Invalid Date"));
                    }else{
                        self.ksDateFilterSelection = $(self.header.el).find('.ks_date_filter_selected').attr('id');
                        self.ksDateFilterStartDate = start_date;
                        self.ksDateFilterEndDate = end_date;
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
                        self.dn_state['user_context']=context
                            $(self.header.el).find(".apply-dashboard-date-filter").addClass("ks_hide");
                            $(self.header.el).find(".clear-dashboard-date-filter").addClass("ks_hide");
                            self.state.ksDateFilterSelection = $(self.header.el).find('.ks_date_filter_selected').attr('id');
                            self.state.pre_defined_filter = {}
                            self.state.ksDateFilterStartDate = parseDateTime(self.ksDateFilterStartDate,self.datetime_format);
                            self.state.ksDateFilterEndDate = parseDateTime(self.ksDateFilterEndDate,self.datetime_format);
                   }
                } else {
                    alert(_t("Start date should be less than end date"));
                }
            } else {
                alert(_t("Please enter start date and end date"));
            }
        }
    }

    _onKsClearDateValues(ks_l_none=false) {
        var self = this;
        self.ksDateFilterSelection = 'l_none';
        self.ksDateFilterStartDate = false;
        self.ksDateFilterEndDate = false;
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
        self.dn_state['user_context']=context
            $('.ks_date_input_fields').addClass("ks_hide");
            $('.ks_date_filter_dropdown').removeClass("ks_btn_first_child_radius");
            self.state.ksDateFilterSelection = 'l_none';
            self.state.pre_defined_filter = {}
        $(self.header.el).find(".apply-dashboard-date-filter").addClass("ks_hide");
        $(self.header.el).find(".clear-dashboard-date-filter").addClass("ks_hide");

    }

    ksSortItems(ks_item_data) {
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
    }


    onKsDuplicateItemClick(e) {
        var self = this;
        var ks_item_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).parent().attr('id');
        var dashboard_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select').val();
        var dashboard_name = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').text();
        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/copy",{
            model: 'ks_dashboard_ninja.item',
            method: 'copy',
            args: [parseInt(ks_item_id), {
                'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
            }],
            kwargs:{},
        }).then(function(result) {
            self.notification.add(_t('Selected item is duplicated to ' + dashboard_name + ' .'),{
                title:_t("Item Duplicated"),
                type: 'success',
            });
                            var js_id = self.actionService.currentController.jsId
                            self.actionService.restore(js_id)

            })
            e.stopPropagation()

    }

    onKsMoveItemClick(e) {
        var self = this;
        var ks_item_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).parent().attr('id');
        var dashboard_id = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select').val();
        var dashboard_name = $($(e.target).parentsUntil(".ks_dashboarditem_id").slice(-1)[0]).find('.ks_dashboard_select option:selected').text();
        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/write",{
            model: 'ks_dashboard_ninja.item',
            method: 'write',
            args: [parseInt(ks_item_id), {
                'ks_dashboard_ninja_board_id': parseInt(dashboard_id)
            }],
            kwargs:{}
        }).then(function(result) {
            self.notification.add(_t('Selected item is moved to ' + dashboard_name + ' .'),{
                title:_t("Item Moved"),
                type: 'success',
            });

                    var js_id = self.actionService.currentController.jsId
                    self.actionService.restore(js_id)

        });
        e.stopPropagation()
    }

     _onKsItemClick(e){
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
                        self.actionService.doAction(action,{})
                    }else{
                        self.actionService.doAction(action, {
                            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                        });
                    }
                }
            }
        } else {
            self.ksAllowItemClick = true;
        }
    }
    ks_dashboard_item_action(e){
        this.ksAllowItemClick = false;
        e.stopPropagation();
    }

    _onKsDeleteItemClick(e) {
        var self = this;
        var item = $($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0])
        var id = parseInt($($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0]).attr('gs-id'));
        self.ks_delete_item(id, item);
        e.stopPropagation();
    }

    ks_delete_item(id, item) {
        var self = this;
        this.dialogService.add(ConfirmationDialog, {
        body: _t("Are you sure that you want to remove this item?"),
        confirm: () => {
            self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/unlink",{
                model: 'ks_dashboard_ninja.item',
                method: 'unlink',
                args: [id],
                kwargs:{}
            }).then(function(result) {

                        // Clean Item Remove Process.
                self.ks_remove_update_interval();
                delete self.ks_dashboard_data.ks_item_data[id];
                self.grid.removeWidget(item);

                if (Object.keys(self.ks_dashboard_data.ks_item_data).length > 0) {
                    self._ksSaveCurrentLayout();
                }

                var js_id = self.actionService.currentController.jsId
                self.actionService.restore(js_id)

                });

            },
            cancel: () => {},
            });
        }
        removeitems(){
            var self = this;
            var ks_items  = Object.values((self.main_body.el).querySelectorAll(".grid-stack-item"));
            ks_items.forEach((item) =>{
             self.grid.removeWidget(item);
             })
            }

    _ksSetCurrentLayoutClick(){
        var self = this;
        this.ks_dashboard_data.ks_selected_board_id = $(self.header.el).find("#ks_dashboard_layout_dropdown_container .ks_layout_selected").data('ks_layout_id');
        $(self.header.el).find(".ks_dashboard_top_menu .ks_dashboard_top_settings").removeClass("ks_hide");
        $(self.header.el).find(".ks_dashboard_top_menu .ks_am_content_element").removeClass("ks_hide");
        $(self.header.el).find(".ks_dashboard_layout_edit_mode_settings").addClass("ks_hide");
//            $('#ks_dashboard_title_input').val(this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][0]);
        this.ks_dashboard_data.name = this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][0];

        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/update_child_board",{
            model: 'ks_dashboard_ninja.board',
            method: 'update_child_board',
            args: ['update', self.ks_dashboard_id, {
                "ks_selected_board_id": this.ks_dashboard_data.ks_selected_board_id,
            }],
            kwargs:{},
        }).then(function(result){
            window.location.reload();
        });
    }

    _ksSetDiscardCurrentLayoutClick(){
        this.ksOnLayoutSelection(this.ks_dashboard_data.ks_selected_board_id);
        $(this.header.el).find(".ks_dashboard_top_menu .ks_dashboard_top_settings").removeClass("ks_hide");
        $(this.header.el).find(".ks_dashboard_top_menu .ks_am_content_element").removeClass("ks_hide");
        $(this.header.el).find(".ks_dashboard_layout_edit_mode_settings").addClass("ks_hide");
    }

    _ksSaveCurrentLayout() {
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
        if (!isMobileOS()) {
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.child_board/write",{
                model: 'ks_dashboard_ninja.child_board',
                method: 'write',
                args: [rec_id, {
                    "ks_gridstack_config": JSON.stringify(grid_config)
                }],
                kwargs:{}
            });
        }
    }

    ks_get_current_gridstack_config(){
        var self = this;
        if (document.querySelector('.grid-stack') && document.querySelector('.grid-stack').gridstack){
            var items = document.querySelector('.grid-stack').gridstack.el.gridstack.engine.nodes;
        }
        var grid_config = {}

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
    }

        ////////////////////////////// Export functions ////////////////////////////////////////////
    async ksChartExportXlsCsv(e) {
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
        const blockUI = new BlockUI();
        await download({
            url: '/ks_dashboard_ninja/export/' + e.currentTarget.dataset.format,
            data: {
                data: JSON.stringify(data)
            },
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }

    ksChartExportPdf (e){
        var self = this;
        var chart_id = e.currentTarget.dataset.chartId;
        var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
        var base64_image
        base64_image = $($(e.target).parentsUntil(".grid-stack-item").slice(-1)[0]).find("canvas")[0].toDataURL("image/png")
        var $ks_el = $($($(self.main_body.el).find(".grid-stack-item[gs-id=" + chart_id + "]")).find('.ks_chart_card_body'));
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
    }
    ksChartExportimage(e){
        var self = this;
        var chart_id = e.currentTarget.dataset.chartId;
        var name = this.ks_dashboard_data.ks_item_data[chart_id].name;
        var base64_image
        base64_image = $($(e.target).parentsUntil(".grid-stack-item").slice(-1)[0]).find("canvas")[0].toDataURL("image/png")
        const link = document.createElement('a');
        link.href =  base64_image;
        link.download = name + 'png'
        document.body.appendChild(link);
        link.click()
        document.body.removeChild(link);
    }
    async ksItemExportJson(e) {
        var itemId = $(e.target).parents('.ks_dashboard_item_button_container')[0].dataset.item_id;
        var name = this.ks_dashboard_data.ks_item_data[itemId].name;
        var data = {
            'header': name,
            item_id: itemId,
        }
        const blockUI = new BlockUI();
        await download({
            url: '/ks_dashboard_ninja/export/item_json',
            data: {
                data: JSON.stringify(data)
            },
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
        e.stopPropagation();
    }
    ksRenderChartColorOptions(e) {
        var self = this;
        if (!$(e.currentTarget).parent().hasClass('ks_date_filter_selected')) {
            //            FIXME : Correct this later.
            var $parent = $(e.currentTarget).parent().parent();
            $parent.find('.ks_date_filter_selected').removeClass('ks_date_filter_selected')
            $(e.currentTarget).parent().addClass('ks_date_filter_selected')
            var item_data = self.ks_dashboard_data.ks_item_data[$parent.data().itemId];
            var chart_data = JSON.parse(item_data.ks_chart_data);
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/write",{
                    model: 'ks_dashboard_ninja.item',
                    method: 'write',
                    args: [$parent.data().itemId, {
                        "ks_chart_item_color": e.currentTarget.dataset.chartColor
                    }],
                    kwargs:{}
            }).then(function() {
                    self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_chart_item_color'] = e.target.dataset.chartColor;
                    $(self.main_body.el).find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();

                    var js_id = self.actionService.currentController.jsId
                    self.actionService.restore(js_id)

            })
        }
    }


    ksOnDashboardExportClick(ev){
        ev.preventDefault();
        var self= this;
        var dashboard_id = JSON.stringify(this.ks_dashboard_id);
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_dashboard_export", {
            model: 'ks_dashboard_ninja.board',
            method: "ks_dashboard_export",
            args: [dashboard_id],
            kwargs: {dashboard_id: dashboard_id}
        }).then(function(result) {
            var name = "dashboard_ninja";
            var data = {
                "header": name,
                "dashboard_data":
                result,
            }
            download({
            data: {
                data:JSON.stringify(data)
            },
                url: '/ks_dashboard_ninja/export/dashboard_json',
            });
        });
    }
    stoppropagation(ev){
        ev.stopPropagation();
    }

    ksOnDashboardImportClick(ev){
        ev.preventDefault();
        var self = this;
        var dashboard_id = this.ks_dashboard_id;
        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_open_import", {
            model: 'ks_dashboard_ninja.board',
            method: 'ks_open_import',
            args: [dashboard_id],
            kwargs: {
                dashboard_id: dashboard_id
            }
        }).then((result)=>{
             self.actionService.doAction(result)
        });
    }

    _ksOnDnLayoutMenuSelect(ev){
        var selected_layout_id = $(ev.currentTarget).data('ks_layout_id');
        this.ksOnLayoutSelection(selected_layout_id);
    }

    ksOnLayoutSelection(layout_id){
        var self = this;
        var selected_layout_name = this.ks_dashboard_data.ks_child_boards[layout_id][0];
        var selected_layout_grid_config = this.ks_dashboard_data.ks_child_boards[layout_id][1];
        this.gridstackConfig = JSON.parse(selected_layout_grid_config);
        Object.entries(this.gridstackConfig).forEach((x,y)=>{
            self.grid.update($(self.main_body.el).find(".grid-stack-item[gs-id=" + x[0] + "]")[0],{ x:x[1]['x'], y:x[1]['y'], w:x[1]['w'], h:x[1]['h'],autoPosition:false});
        });


//            this.ks_dashboard_data.ks_selected_board_id = layout_id;
        $(self.header.el).find("#ks_dashboard_layout_dropdown_container .ks_layout_selected").removeClass("ks_layout_selected");
        $(self.header.el).find("li.ks_dashboard_layout_event[data-ks_layout_id='"+ layout_id + "']").addClass('ks_layout_selected');
        $(self.header.el).find("#ks_dn_layout_button span:first-child").text(selected_layout_name);
        $(self.header.el).find(".ks_add_item_type_button").addClass("ks_hide");
        $(self.header.el).find("#ks_ai_item_dash").addClass("ks_hide");
//        $(self.header.el).find(".ks_dashboard_top_menu .ks_dashboard_edit_layout").removeClass("ks_hide");
        $(self.header.el).find(".ks_dashboard_top_menu .ks_am_content_element").addClass("ks_hide");

        $(self.header.el).find(".ks_dashboard_layout_edit_mode_settings").removeClass("ks_hide");
    }

    _onKsSaveLayoutClick(){
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
            var new_model = `web/dataset/call_kw/${model}/write`
            this._rpc(new_model,{
                model: model,
                method: 'write',
                args: [rec_id, {
                    'name': dashboard_title
                }],
                kwargs : {},
            })
        }
        if (this.ks_dashboard_data.ks_item_data) self._ksSaveCurrentLayout();
        self._ksRenderActiveMode();
    }

    _onKsCancelLayoutClick(){
        var self = this;
        //        render page again

        var js_id = self.actionService.currentController.jsId
        self.actionService.restore(js_id)

    }

    _onKsCreateLayoutClick() {
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
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/update_child_board",{
                model: 'ks_dashboard_ninja.board',
                method: 'update_child_board',
                args: ['create', self.ks_dashboard_id, {
                    "ks_gridstack_config": JSON.stringify(grid_config),
                    "ks_dashboard_ninja_id": self.ks_dashboard_id,
                    "name": dashboard_title,
                    "ks_active": true,
                    "company_id": self.ks_dashboard_data.ks_company_id,
                }],
                kwargs : {},
            }).then(function(res_id){
                self.ks_update_child_board_value(dashboard_title, res_id, grid_config),
                self._ksRenderActiveMode();
                window.location.reload();
            });
        }
    }
    ks_update_child_board_value(dashboard_title, res_id, grid_config){
        var self = this;
        var child_board_id = res_id.toString();
        self.ks_dashboard_data.ks_selected_board_id = child_board_id;
        var update_data = {};
        update_data[child_board_id] = [dashboard_title, JSON.stringify(grid_config)];
        self.ks_dashboard_data.ks_child_boards = Object.assign(update_data,self.ks_dashboard_data.ks_child_boards);
    }

    _ksRenderActiveMode(){
        var self = this
        self.ks_mode = 'active';

        if (self.grid && $('.grid-stack').data('gridstack')) {
            $('.grid-stack').data('gridstack').disable();
        }

        if (self.ks_dashboard_data.ks_child_boards) {
//            var $layout_container = $(QWeb.render('ks_dn_layout_container', {
//                ks_selected_board_id: self.ks_dashboard_data.ks_selected_board_id,
//                ks_child_boards: self.ks_dashboard_data.ks_child_boards,
//                ks_multi_layout: self.ks_dashboard_data.multi_layouts,
//                ks_dash_name: self.ks_dashboard_data.name
//            }));
//            $('#ks_dashboard_title .ks_am_element').replaceWith($layout_container);
//            $('#ks_dashboard_title_label').replaceWith($layout_container);
            var $layout_container = $(renderToElement('ks_dn_layout_container_new', {
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
        if (self.ks_dashboard_data.ks_item_data) $('.ks_am_content_element').addClass("ks_hide");

        $(self.main_body.el).find('.ks_item_not_click').addClass('ks_item_click').removeClass('ks_item_not_click')
        $(self.main_body.el).find('.ks_dashboard_item').addClass('ks_dashboard_item_header_hover')
        $(self.main_body.el).find('.ks_dashboard_item_header').addClass('ks_dashboard_item_header_hover')

        $(self.main_body.el).find('.ks_dashboard_item_l2').addClass('ks_dashboard_item_header_hover')
        $(self.main_body.el).find('.ks_dashboard_item_header_l2').addClass('ks_dashboard_item_header_hover')

        //      For layout 5
        $(self.main_body.el).find('.ks_dashboard_item_l5').addClass('ks_dashboard_item_header_hover')


        $(self.main_body.el).find('.ks_dashboard_item_button_container').addClass('ks_dashboard_item_header_hover');

        $(self.header.el).find('.ks_dashboard_top_settings').removeClass("ks_hide")
        $(self.header.el).find('.ks_dashboard_edit_mode_settings').addClass("ks_hide")

        $(self.main_body.el).find('.ks_start_tv_dashboard').removeClass('ks_hide');
        $(self.main_body.el).find('.ks_chart_container').removeClass('ks_item_not_click ks_item_click');
        $(self.main_body.el).find('.ks_list_view_container').removeClass('ks_item_click');


        self.grid.commit();
    }

    ks_remove_update_interval(){
        var self = this;
        if (self.ksUpdateDashboard) {
            Object.values(self.ksUpdateDashboard).forEach(function(itemInterval) {
                clearInterval(itemInterval);
            });
            self.ksUpdateDashboard = {};
        }
    }

    onKsEditLayoutClick(e) {
        var self = this;
        self.grid.setStatic(false);
        self._ksRenderEditMode();
    }

    _ksRenderEditMode(){
        var self = this;
        self.ks_mode = 'edit';
        self.ks_remove_update_interval();

        // Update the value of an input element with the ID 'ks_dashboard_title_input'
        // using the current dashboard name
        $('#ks_dashboard_title_input').val(self.ks_dashboard_data.name);

        // Hide and show certain elements based on the edit mode
        $('.ks_am_element').addClass("ks_hide");
        $('.ks_em_element').removeClass("ks_hide");
        $('.ks_dashboard_print_pdf').addClass("ks_hide");

        // Update classes for various dashboard elements to control their styling
        $(self.main_body.el).find('.ks_item_click').addClass('ks_item_not_click').removeClass('ks_item_click');
        $(self.main_body.el).find('.ks_dashboard_item').removeClass('ks_dashboard_item_header_hover');
        $(self.main_body.el).find('.ks_dashboard_item_header').removeClass('ks_dashboard_item_header_hover');
        $(self.main_body.el).find('.ks_dashboard_item_l2').removeClass('ks_dashboard_item_header_hover');
        $(self.main_body.el).find('.ks_dashboard_item_header_l2').removeClass('ks_dashboard_item_header_hover');
        $(self.main_body.el).find('.ks_dashboard_item_l5').removeClass('ks_dashboard_item_header_hover');
        $(self.main_body.el).find('.ks_dashboard_item_button_container').removeClass('ks_dashboard_item_header_hover');

//        $(self.header.el).find('.ks_dashboard_link').addClass("ks_hide")
        $(self.header.el).find('.ks_dashboard_top_settings').addClass("ks_hide")
        $(self.header.el).find('.ks_dashboard_edit_mode_settings').removeClass("ks_hide")

        // Hide elements related to TV dashboard and make certain elements not clickable
        $(self.main_body.el).find('.ks_start_tv_dashboard').addClass('ks_hide');
        $(self.main_body.el).find('.ks_chart_container').addClass('ks_item_not_click');
        $(self.main_body.el).find('.ks_list_view_container').addClass('ks_item_not_click');

        if (self.grid) {
            self.grid.enable();
        }
    }


    onAddItemTypeClick(e) {
        var self = this;
             self.dialogService.add(FormViewDialog,{
                resModel: 'ks_dashboard_ninja.item',
                context: {
                    'ks_dashboard_id': self.ks_dashboard_id,
                    'ks_dashboard_item_type': 'ks_tile',
                    'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                    'form_view_initial_mode': 'edit',
                    'ks_set_interval': self.ks_dashboard_data.ks_set_interval,
                    'ks_data_formatting':self.ks_dashboard_data.ks_data_formatting,
                    'ks_form_view' : true
                },
                onRecordSaved:()=>{
                            var js_id = self.actionService.currentController.jsId
                            self.actionService.restore(js_id)
                            $('body').removeClass('ks_dn_create_chart')

                    },
                onRecordDiscarded:()=>{
                    $('body').removeClass('ks_dn_create_chart')
                }
            });

    }

    ksImportItemJson(e) {
        var self = this;
        $('.ks_input_import_item_button').click();
    }

     ksImportItem(e) {
        var self = this;
        var fileReader = new FileReader();
        fileReader.onload = function() {
            $('.ks_input_import_item_button').val('');
            self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_import_item", {
            model: 'ks_dashboard_ninja.board',
            method: 'ks_import_item',
            args: [self.ks_dashboard_id],
            kwargs: {
                file: fileReader.result,
                dashboard_id: self.ks_dashboard_id
            }
            }).then(function(result) {
                if (result === "Success") {

                var js_id = self.actionService.currentController.jsId
                self.actionService.restore(js_id)
                }
            });
        };
        fileReader.readAsText($('.ks_input_import_item_button').prop('files')[0]);
    }


    ksOnDashboardSettingClick(ev){
        var self= this;
        var dashboard_id = this.ks_dashboard_id;
        var action = {
            name: _t('ks_open_setting'),
            type: 'ir.actions.act_window',
            res_model: 'ks_dashboard_ninja.board',
            res_id: dashboard_id,
            domain: [],
            context: {'create':false},
            views: [
                [false, 'form']
            ],
            view_mode: 'form',
            target: 'new',
        }
        self.actionService.doAction(action)
    }

    ksOnDashboardDeleteClick(ev){
        ev.preventDefault();
        var dashboard_id = this.ks_dashboard_id;
        var self= this;
        self.dialogService.add(ConfirmationDialog, {
            body: _t("Are you sure you want to delete this dashboard ?"),
            confirm: () => {
                this._rpc("/web/dataset/call_kw/ks.dashboard.delete.wizard/ks_delete_record", {
                    model: 'ks.dashboard.delete.wizard',
                    method: "ks_delete_record",
                    args: [self.ks_dashboard_id],
                    kwargs: {dashboard_id: dashboard_id}
                }).then((result)=>{
                self.actionService.doAction(result)
                });
            },
        });
    }

    ksOnDashboardCreateClick(ev){
        var self= this;
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
        self.actionService.doAction(action)
    }

    ksOnDashboardDuplicateClick(ev){
        ev.preventDefault();
        var self= this;
        var dashboard_id = this.ks_dashboard_id;
        this._rpc('/web/dataset/call_kw/ks.dashboard.duplicate.wizard/DuplicateDashBoard', {
            model: 'ks.dashboard.duplicate.wizard',
            method: "DuplicateDashBoard",
            args: [self.ks_dashboard_id],
            kwargs: {}
        }).then((result)=>{
            self.actionService.doAction(result)
        });
   }

    onEditItemTypeClick(ev) {
        this.ksAllowItemClick = false;
        var self =this
        if(ev.currentTarget.dataset.itemId){
            self.dialogService.add(FormViewDialog,{
                resModel: 'ks_dashboard_ninja.item',
                    resId : parseInt(ev.currentTarget.dataset.itemId),
                    context: {
                        'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                        'form_view_initial_mode': 'edit',
                        'ks_form_view' :true
                    },
                onRecordSaved:()=>{

                            var js_id = self.actionService.currentController.jsId
                            self.actionService.restore(js_id)
                            $('body').removeClass('ks_dn_create_chart')
                    },
                    onRecordDiscarded:()=>{
                        $('body').removeClass('ks_dn_create_chart')
                    }
            });
        }

    }
        kscreateaiitem(ev){
            var self= this;
            self.dialogService.add(FormViewDialog,{
                resModel: 'ks_dashboard_ninja.arti_int',
                context: {
                    'ks_dashboard_id': self.ks_dashboard_id,
                    'ks_form_view' : true
                },
            });
        }
    kscreateaidashboard(ev){
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
           self.actionService.doAction(action)
        }





}

KsDashboardNinja.components = { Ksdashboardtile, Ksdashboardlistview, Ksdashboardgraph, Ksdashboardkpiview, Ksdashboardtodo, DateTimePicker, DateTimeInput};
KsDashboardNinja.template = "ks_dashboard_ninja.KsDashboardNinjaHeader"
registry.category("actions").add("ks_dashboard_ninja", KsDashboardNinja);

const ks_dn_webclient ={
    async loadRouterState(...args) {
        var self = this;
//      const sup = await this.super(...args);
        const sup = await super.loadRouterState(...args);
        const ks_reload_menu = async (id) =>  {
            this.menuService.reload().then(() => {
                self.menuService.selectMenu(id);
            });
        }
        this.actionService.ksDnReloadMenu = ks_reload_menu;
        return sup;
    },
};
patch(WebClient.prototype, ks_dn_webclient)