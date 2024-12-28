///** @odoo-module **/
//import { Component, onWillStart, useState ,useEffect, onMounted, onWillRender,useRef,onWillPatch, onRendered } from "@odoo/owl";
//import { localization } from "@web/core/l10n/localization";
//import { formatFloat } from "@web/core/utils/numbers";
//import {formatDate,formatDateTime} from "@web/core/l10n/dates";
//import {parseDateTime,parseDate,} from "@web/core/l10n/dates";
//import { useService } from "@web/core/utils/hooks";
//import { Ksdashboardgraph } from '@ks_dashboard_ninja/components/ks_dashboard_graphs/ks_dashboard_graphs';
//
//export class Ksdashboardlistview extends Component{
//    setup(){
//        super.setup();
//         this._rpc = useService("rpc");
//        onMounted(() => this._update_view());
//        this.state = useState({list_view_data:""})
//        this.item = this.props.item
//        this.ks_dashboard_data = this.props.dashboard_data
//        this.prepare_item();
//        var update_interval = this.props.dashboard_data.ks_set_interval
//        useEffect(()=>{
//            if (update_interval){
//                const interval = setInterval(() => {
//                    this.ksFetchUpdateItem(this.item.id);
//                }, update_interval);
//                return () => clearInterval(interval);
//            }
//
//        })
//    }
//       ksFetchUpdateItem(item_id) {
//            var self = this;
//            return self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_fetch_item",{
//                model: 'ks_dashboard_ninja.board',
//                method: 'ks_fetch_item',
//                args: [
//                    [parseInt(item_id)], self.ks_dashboard_data.ks_dashboard_id,{}
//                ],
//                kwargs:{},
////                context: self.getContext(),
//            }).then(function(new_item_data) {
//                this.ks_dashboard_data.ks_item_data[item_id] = new_item_data[item_id];
//                this.item = this.ks_dashboard_data.ks_item_data[item_id] ;
//                this.prepare_item()
//            }.bind(this));
//        }
//    _update_view(){
//        if (this.item.ks_pagination_limit < this.intial_count) {
//            $('.ks_load_next').addClass('ks_event_offer_list');
//        }
//        if (this.intial_count < this.item.ks_pagination_limit ) {
//            $('.ks_load_next').addClass('ks_event_offer_list');
//        }
//        if (this.item.ks_record_data_limit === this.item.ks_pagination_limit){
//               $('.ks_load_next').addClass('ks_event_offer_list');
//        }
//        if (this.intial_count == 0){
//            $('.ks_pager').addClass('d-none');
//        }
//        if (this.item.ks_pagination_limit==0){
//            $('.ks_pager_name').addClass('d-none');
//        }
//        if (this.item.ks_data_calculation_type === 'query' || this.item.ks_list_view_type === "ungrouped"){
//            $('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
//        }
//        if (!this.item.ks_show_records) {
//            $('#ks_item_info').hide();
//        }
//    }
//
//    get ksIsDashboardManager(){
//        return this.ks_dashboard_data.ks_dashboard_manager;
//    }
//
//    get ksIsUser(){
//        return true;
//    }
//
//    get ks_dashboard_list(){
//        return this.ks_dashboard_data.ks_dashboard_list;
//    }
//
//    onChartCanvasClick(evt) {
//
//        var self = this;
//        this.ksUpdateDashboard = {};
//        var item_id = $(evt.target).parent().data().itemId;
//        if (this.ksUpdateDashboard[item_id]) {
//            clearInterval(this.ksUpdateDashboard[item_id]);
//            delete self.ksUpdateDashboard[item_id];
//        }
//        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
//        if (self.ks_dashboard_data.ks_item_data[item_id].max_sequnce) {
//
//            var sequence = item_data.sequnce ? item_data.sequnce : 0
//
//            var domain = $(evt.target).parent().data().domain;
//
//            if ($(evt.target).parent().data().last_seq !== sequence) {
//                self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
//                    model: 'ks_dashboard_ninja.item',
//                    method: 'ks_fetch_drill_down_data',
//                    args: [item_id, domain, sequence],
//                    kwargs : {},
//                }).then(function(result) {
//                    if (result.ks_list_view_data) {
//                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
//                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
//                        } else {
//                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
//                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
//                        }
//                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
//                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
//                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
//                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
//                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
//                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
//
//                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
//                        var $container = self.renderListViewData(item_data);
//                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
//                    } else {
//                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
//                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
//                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
//                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
//                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
//                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
//                        } else {
//                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
//                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
//                        }
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
//                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
////                        self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]), item_data);
//                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
//                        Ksdashboardgraph.prototype.ks_render_graphs($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data);
//
//                    }
//                });
//            }
//        }
//        evt.stopPropagation();
//    }
//
//    prepare_item() {
//        var self = this;
//        if (this.item.ks_info){
//            var ks_description = this.item.ks_info.split('\n');
//            var ks_description = ks_description.filter(element => element !== '')
//        }else {
//            var ks_description = false;
//        }
//
//        var list_view_data = JSON.parse(this.item.ks_list_view_data),
//            data_rows = list_view_data.data_rows,
//            length = data_rows ? data_rows.length: false;
//        this.ks_info = ks_description;
//        this.ks_chart_title = this.item.name
//        this.item_id = this.item.id
//        this.count = '1-' + length
//        this.offset = 1
//        this.intial_count = length
//        this.ks_pager = true
//        this.ks_company= this.item.ks_company
//        this.calculation_type = this.ks_dashboard_data.ks_item_data[this.item_id].ks_data_calculation_type
//
//        if (this.item.ks_list_view_type === "ungrouped" && list_view_data) {
//            if (list_view_data.date_index) {
//                var index_data = list_view_data.date_index;
//                for (var i = 0; i < index_data.length; i++) {
//                    for (var j = 0; j < list_view_data.data_rows.length; j++) {
//                        var index = index_data[i]
//                        var date = list_view_data.data_rows[j]["data"][index]
//                        if (date) {
//                            if( list_view_data.fields_type[index] === 'date'){
//                                list_view_data.data_rows[j]["data"][index] = formatDate(parseDate(date), { format: localization.dateFormat })
//                            } else{
//                                list_view_data.data_rows[j]["data"][index] = formatDateTime(parseDateTime(date), { format: localization.dateTimeFormat })
//                            }
//                        }else{
//                            list_view_data.data_rows[j]["data"][index] = "";
//                        }
//                    }
//                }
//            }
//        }
//        if (list_view_data) {
//            for (var i = 0; i < list_view_data.data_rows.length; i++) {
//                for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
//                    if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
//                        if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
//                            list_view_data.data_rows[i].data[j] = formatFloat(list_view_data.data_rows[i].data[j], Float64Array, {digits:[0, self.item.ks_precision_digits]})
//                        }
//                    } else {
//                        list_view_data.data_rows[i].data[j] = "";
//                    }
//                }
//            }
//        }
//        this.state.list_view_data = list_view_data
//        this.list_type = this.item.ks_list_view_type
//        this.tmpl_list_type = self.ks_dashboard_data.ks_item_data[this.item_id].ks_list_view_type
//        this.isDrill = this.ks_dashboard_data.ks_item_data[this.item_id]['isDrill']
////        this.ks_dashboard_data = this.ks_dashboard_data
////        this.item.$el = $ks_gridstack_container;
//
//    }
//};
//Ksdashboardlistview.components = { Ksdashboardgraph };
//Ksdashboardlistview.props = {
//    item: { type: Object, Optional:true},
//    dashboard_data: { type: Object, Optional:true},
//};
//
//Ksdashboardlistview.template = "Ksdashboardlistview";
////registry.category("actions").add("ks_dashboard_ninja", Ksdashboardlistview);