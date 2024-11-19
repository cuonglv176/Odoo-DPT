/** @odoo-module **/
import { Component,useState ,onWillUpdateProps,useEffect,onMounted,useRef} from "@odoo/owl";
import {globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions';
import { formatFloat } from "@web/core/utils/numbers";
import { formatInteger } from "@web/views/fields/formatters";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

export class Ksdashboardkpiview extends Component{
        file_type_magic_word= {'/': 'jpg','R': 'gif','i': 'png','P': 'svg+xml'}
    setup(){
        var self = this;
        this._rpc = useService("rpc");
        this.actionService = useService("action");
        this.ks_kpi = useRef('ks_kpi')
        this.state = useState({item_info_kpi1:{},item_info_kpi2:{},item_info_kpi3:{}})
        onMounted(() => this._update_view());
        this.item = this.props.item
        this.ks_dashboard_data = this.props.dashboard_data
        this.prepareKpiData();
        var update_interval = this.props.dashboard_data.ks_set_interval
        onWillUpdateProps(async(nextprops)=>{
            if(nextprops.ksdatefilter !='none'){
                await this.ksFetchUpdateItem(this.item.id)
            }
            if (Object.keys(nextprops.pre_defined_filter).length){
                if (nextprops.pre_defined_filter?.item_ids?.includes(this.item.id)){
                    await this.ksFetchUpdateItem(this.item.id)
                }
            }

        })
        useEffect(()=>{
            if (update_interval){
                const interval = setInterval(() => {
                    this.ksFetchUpdateItem(this.item.id);
                }, update_interval);
                return () => clearInterval(interval);
            }

        })
    }
    ksFetchUpdateItem(item_id) {
            var self = this;
            return jsonrpc("/web/dataset/call_kw",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_item',
                args: [
                    [parseInt(item_id)], self.ks_dashboard_data.ks_dashboard_id,self.__owl__.parent.component.ksGetParamsForItemFetch(self.item.id)
                ],
                kwargs:{context:this.props.dashboard_data.context},
            }).then(function(new_item_data) {
                this.ks_dashboard_data.ks_item_data[item_id] = new_item_data[item_id];
                this.item = this.ks_dashboard_data.ks_item_data[item_id] ;
               this.__owl__.parent.component.ks_dashboard_data.ks_item_data[this.item.id] = new_item_data[item_id]
                this.prepareKpiData()
            }.bind(this));
        }


    _update_view(){
        if(!this.kpi_data[1]){
            if (this.field.ks_target_view === "Progress Bar" && this.field.ks_goal_enable) {
                $('#ks_progressbar').val(parseInt(this.state.item_info_kpi1.target_progress_deviation));
            }
            if (this.field.ks_goal_enable) {
                    if (this.state.item_info_kpi1.pre_arrow == 'up') {
                        $('#' + this.item.id).find(".target_deviation").css({
                            "color": "green",
                        });
                    } else {
                        $('#' + this.item.id).find(".target_deviation").css({
                            "color": "red",
                        });
                    }
                }
            var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
            if (this.field.ks_previous_period && String(this.state.item_info_kpi1.previous_period_data) && ks_valid_date_selection.indexOf(this.ks_date_filter_selection) >= 0) {
                if (this.state.item_info_kpi1.pre_arrow == 'up') {
                    $('#' + this.item.id).find(".pre_deviation").css({
                        "color": "green",
                    });
                } else {
                    $('#' + this.item.id).find(".pre_deviation").css({
                        "color": "red",
                    });
                }
            }
            if ($('#' + this.item.id).find('.ks_target_previous').children().length !== 2) {
                $('#' + this.item.id).find('.ks_target_previous').addClass('justify-content-center');
            }
        }else{
            if(this.field.ks_data_comparison == 'Sum'){
                $('#' + this.item.id).find('.target_deviation').css({
                    "color": this.state.item_info_kpi2.ks_color
                });
                if (this.field.ks_target_view === "Progress Bar") {
                    $('#' + this.item.id).find('#ks_progressbar').val(target_progress_deviation)
                }
            }
            if(this.field.ks_data_comparison == 'Percentage'){
                $('#' + this.item.id).find('.target_deviation').css({
                    "color": this.state.item_info_kpi2.ks_color
                });
                if (this.field.ks_target_view === "Progress Bar") {
                    if (this.state.item_info_kpi2.count) $('#' + this.item.id).find('#ks_progressbar').val(this.state.item_info_kpi2.count);
                    else $('#' + this.item.id).find('#ks_progressbar').val(0);
                }
            }
        }

        $(this.ks_kpi.el).find('.ks_dashboarditem_id').css({
            "background-color": this.ks_rgba_background_color,
            "color": this.ks_rgba_font_color,
        });
    }

    ksSum(count_1, count_2, item_info, field, target_1, kpi_data) {
        var self = this;
        var count = count_1 + count_2;
        if (field.ks_multiplier_active){
            item_info['count'] = globalfunction._onKsGlobalFormatter(count* field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
            item_info['count_tooltip'] = formatFloat(count * field.ks_multiplier,{digits:[0,field.ks_precision_digits]});
        }else{

            item_info['count'] = globalfunction._onKsGlobalFormatter(count, field.ks_data_formatting, field.ks_precision_digits);
            item_info['count_tooltip'] = formatFloat(parseFloat(count), Float64Array, {digits:[0,field.ks_precision_digits]});
        }
         if (field.ks_multiplier_active){
            count = count * field.ks_multiplier;
        }
        var ks_selection = field.ks_unit_selection;
        if (ks_selection === 'monetary') {
            var ks_currency_id = field.ks_currency_id[0];
            var ks_data = globalfunction.ks_monetary(item_info['count'], ks_currency_id);
            item_info['count'] = ks_data;
        } else if (ks_selection === 'custom') {
            var ks_field = field.ks_chart_unit;
           item_info['count']= ks_field+" "+item_info['count']
        }

        item_info['target_enable'] = field.ks_goal_enable;
        item_info['ks_color'] = (target_1 - count) > 0 ? "red" : "green";
        item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
        item_info['ks_comparison'] = true;
        var target_deviation = (target_1 - count) > 0 ? Math.round(((target_1 - count) / target_1) * 100) : Math.round((Math.abs((target_1 - count)) / target_1) * 100);
        if (target_deviation !== Infinity) item_info.target_deviation = formatInteger(target_deviation) + "%";
        else {
            item_info.target_deviation = target_deviation;
            item_info.pre_arrow = false;
        }
        var target_progress_deviation = target_1 == 0 ? 0 : Math.round((count / target_1) * 100);
        item_info.target_progress_deviation = formatInteger(target_progress_deviation) + "%";
        return item_info
    }

    ksPercentage(count_1, count_2, field, item_info, target_1, kpi_data) {
        if (field.ks_multiplier_active){
            count_1 = count_1 * field.ks_multiplier;
            count_2 = count_2 * field.ks_multiplier;
        }
        var count = parseInt((count_1 / count_2) * 100);
        if (field.ks_multiplier_active){
            count = count * field.ks_multiplier;
        }
        item_info['count'] = count ? formatInteger(count) + "%" : "0%";
        item_info['count_tooltip'] = count ? count + "%" : "0%";
        item_info.target_progress_deviation = item_info['count']
        target_1 = target_1 > 100 ? 100 : target_1;
        item_info.target = target_1 + "%";
        item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
        item_info['ks_color'] = (target_1 - count) > 0 ? "red" : "green";
        item_info['target_enable'] = field.ks_goal_enable;
        item_info['ks_comparison'] = false;
        item_info.target_deviation = item_info.target > 100 ? 100 : item_info.target;
        return item_info
    }

    prepareKpiData() {
        var self = this;
        var field = this.item;
        this.ks_date_filter_selection = field.ks_date_filter_selection;
        if (field.ks_date_filter_selection === "l_none") this.ks_date_filter_selection = self.ks_dashboard_data.ks_date_filter_selection;
        var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
        var kpi_data = JSON.parse(field.ks_kpi_data);
        var count_1 = kpi_data[0] ? kpi_data[0].record_data: undefined;
        var count_2 = kpi_data[1] ? kpi_data[1].record_data : undefined;
        var target_1 = kpi_data[0] ? kpi_data[0].target : undefined;
        var target_view = field.ks_target_view,
            pre_view = field.ks_prev_view;
        this.ks_rgba_background_color = self._ks_get_rgba_format(field.ks_background_color);
        var ks_rgba_button_color = self._ks_get_rgba_format(field.ks_button_color);
        this.ks_rgba_font_color = self._ks_get_rgba_format(field.ks_font_color);
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
            if (deviation !== Infinity) deviation = deviation ? formatInteger(deviation) + '%' : 0 + '%';
        }
        if (field.ks_previous_period && ks_valid_date_selection.indexOf(this.ks_date_filter_selection) >= 0) {
            var previous_period_data = kpi_data[0].previous_period;
            var pre_diffrence = (count_1 - previous_period_data);
            if (field.ks_multiplier_active){
                var previous_period_data = kpi_data[0].previous_period * field.ks_multiplier;
                var pre_diffrence = (count_1 * field.ks_multiplier   - previous_period_data);
            }
            var pre_acheive = pre_diffrence > 0 ? true : false;
            pre_diffrence = Math.abs(pre_diffrence);
            var pre_deviation = previous_period_data ? formatInteger(parseInt((pre_diffrence / previous_period_data) * 100)) + '%' : "100%"
        }
        if (this.item.ks_info){
            var ks_description = this.item.ks_info.split('\n');
            var ks_description = ks_description.filter(element => element !== '')
        }else {
            var ks_description = false;
        }
        this.item['ksIsDashboardManager'] = self.ks_dashboard_data.ks_dashboard_manager;
        this.item['ksIsUser'] = true;
//        if (this.item.ks_tv_play){
//            this.item['ksIsUser'] = false;
//        }
        var ks_icon_url;
        if (field.ks_icon_select == "Custom") {
            if (field.ks_icon[0]) {
                ks_icon_url = 'data:image/' + (self.file_type_magic_word[field.ks_icon[0]] || 'png') + ';base64,' + field.ks_icon;
            } else {
                ks_icon_url = false;
            }
        }
//            parseInt(Math.round((count_1 / target_1) * 100)) ? formatInteger(Math.round((count_1 / target_1) * 100)) : "0"
        var target_progress_deviation = String(Math.round((count_1  / target_1) * 100));
         if(field.ks_multiplier_active){
            var target_progress_deviation = String(Math.round(((count_1 * field.ks_multiplier) / target_1) * 100));
         }
        var ks_rgba_icon_color = self._ks_get_rgba_format(field.ks_default_icon_color)
        var item_info = {
            item: this.item,
            id: field.id,
            count_1: globalfunction.ksNumFormatter(kpi_data[0]['record_data'], 1),
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
            ks_previous_period: ks_valid_date_selection.indexOf(this.ks_date_filter_selection) >= 0 ? field.ks_previous_period : false,
            target: globalfunction.ksNumFormatter(target_1, 1),
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
        item_info.target_progress_deviation = parseInt(item_info.target_progress_deviation) ? formatInteger(parseInt(item_info.target_progress_deviation)) : "0"
        if (field.ks_multiplier_active){
            item_info['count_1'] = globalfunction._onKsGlobalFormatter(kpi_data[0]['record_data'] * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
            item_info['count_1_tooltip'] = kpi_data[0]['record_data'] * field.ks_multiplier
        }else{
            item_info['count_1'] = globalfunction._onKsGlobalFormatter(kpi_data[0]['record_data'], field.ks_data_formatting, field.ks_precision_digits);
        }
         if (kpi_data[0].target){
            item_info['target'] = globalfunction._onKsGlobalFormatter(kpi_data[0].target, field.ks_data_formatting, field.ks_precision_digits);
        }
        if (field.ks_unit){
            if (field.ks_multiplier_active){
                var ks_record_count = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
                var ks_record_count = kpi_data[0]['record_data']
            }
            var ks_selection = field.ks_unit_selection;
            if (ks_selection === 'monetary') {
                var ks_currency_id = field.ks_currency_id;
                var ks_data = globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
                ks_data = globalfunction.ks_monetary(ks_data, ks_currency_id);
                item_info['count_1'] = ks_data;
            } else if (ks_selection === 'custom') {
                var ks_field = field.ks_chart_unit;
                item_info['count_1']= ks_field+" "+globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            }else {
                item_info['count_1']= globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_formatting, field.ks_precision_digits);
            }
        }
        this.kpi_data = kpi_data
        this.field = field
        this.state.item_info_kpi1 = this.state.item_info_kpi3 = item_info
        if (kpi_data[1]) {
            switch (this.field.ks_data_comparison) {
                case "None":
                    if (field.ks_multiplier_active){
                        var count_tooltip = String(count_1 * field.ks_multiplier) + "/" + String(count_2 * field.ks_multiplier);
                        var count = String(globalfunction.ksNumFormatter(count_1 * field.ks_multiplier, 1)) + "/" + String(globalfunction.ksNumFormatter(count_2 * field.ks_multiplier, 1));
                        var data1 = globalfunction._onKsGlobalFormatter(count_1 * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                        var data2 = globalfunction._onKsGlobalFormatter(count_2 * field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits);
                        if (field.ks_unit){
                            var ks_selection = field.ks_unit_selection;
                            if (ks_selection === 'monetary') {
                                var ks_currency_id = field.ks_currency_id;
                                data1 = globalfunction.ks_monetary(data1, ks_currency_id);
                                data2 = globalfunction.ks_monetary(data2, ks_currency_id)
                                item_info['count'] = data1+"/"+data2;
                            } else if (ks_selection === 'custom') {
                                var ks_field = field.ks_chart_unit;
                                data1= ks_field+" "+data1
                                data2= ks_field+" "+data2
                                item_info['count']= data1+"/"+data2
                            }
                        }else {
                            item_info['count']=String(globalfunction._onKsGlobalFormatter(count_1*field.ks_multiplier, field.ks_data_formatting, field.ks_precision_digits)) + "/" + String(globalfunction._onKsGlobalFormatter(count_2*field.ks_multiplier, field.ks_data_format, field.ks_precision_digits));
                        }
                    }else{
                        var count_tooltip = String(count_1) + "/" + String(count_2);
                        var count = String(globalfunction.ksNumFormatter(count_1, 1)) + "/" + String(globalfunction.ksNumFormatter(count_2, 1));
                        var data1 = globalfunction._onKsGlobalFormatter(count_1 , field.ks_data_formatting, field.ks_precision_digits);
                        var data2 = globalfunction._onKsGlobalFormatter(count_2 , field.ks_data_formatting, field.ks_precision_digits);
                        if (field.ks_unit){
                            var ks_selection = field.ks_unit_selection;
                            if (ks_selection === 'monetary') {
                            var ks_currency_id = field.ks_currency_id;
                            data1 = globalfunction.ks_monetary(data1, ks_currency_id);
                            data2 = globalfunction.ks_monetary(data2, ks_currency_id)
                            item_info['count'] = data1+"/"+data2;
                            } else{
                            var ks_field = field.ks_chart_unit;
                            data1= ks_field+" "+data1
                            data2= ks_field+" "+data2
                            item_info['count']= data1+"/"+data2
                            }
                        }else {
                            item_info['count']=String(globalfunction._onKsGlobalFormatter(count_1, field.ks_data_formatting, field.ks_precision_digits)) + "/" + String(globalfunction._onKsGlobalFormatter(count_2, field.ks_data_formatting, field.ks_precision_digits));
                        }
                    }
                    item_info['count_tooltip'] = count_tooltip;
                    item_info['target_enable'] = false;
                    this.state.item_info_kpi2 = item_info
                    break;
                case "Sum":
                    this.state.item_info_kpi2 = this.ksSum(count_1, count_2, item_info, field, target_1, kpi_data);
                    break;
                case "Percentage":
                    this.state.item_info_kpi2 = this.ksPercentage(count_1, count_2, field, item_info, target_1, kpi_data);
                    break;
                case "Ratio":
                    var gcd = self.ks_get_gcd(Math.round(count_1), Math.round(count_2));
                    if (this.item.ks_data_formatting == 'exact'){
                        if (count_1 && count_2) {
                            item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                            item_info['count'] = formatFloat(count_1 / gcd, Float64Array,{digits: [0, field.ks_precision_digits]}) + ":" + formatFloat(count_2 / gcd, Float64Array, {digits: [0, field.ks_precision_digits]});
                        } else {
                            item_info['count_tooltip'] = count_1 + ":" + count_2;
                            item_info['count'] = count_1 + ":" + count_2
                        }
                    }else{
                        if (count_1 && count_2) {
                            item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                            item_info['count'] = globalfunction.ksNumFormatter(count_1 / gcd, 1) + ":" + globalfunction.ksNumFormatter(count_2 / gcd, 1);
                        }else {
                            item_info['count_tooltip'] = (count_1) + ":" + count_2;
                            item_info['count'] = globalfunction.ksNumFormatter(count_1, 1) + ":" + globalfunction.ksNumFormatter(count_2, 1);
                        }
                    }
                    item_info['target_enable'] = false;
                    this.state.item_info_kpi2 = item_info
                    break;
            }
        }
    }


    _ks_get_rgba_format(val){
        var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
        }).join(",");
        return "rgba(" + rgba + "," + val.split(',')[1] + ")";
    }

    get previewclass(){
        var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
        if (this.field.ks_previous_period && String(this.state.item_info_kpi1.previous_period_data) && ks_valid_date_selection.indexOf(this.ks_date_filter_selection) >= 0 &&
        (this.field.ks_goal_enable && this.field.ks_target_view === "Progress Bar")){
            return 'ks_previous_period'
        }else{ return ''}
    }

    ks_get_gcd(a, b) {
        return (b == 0) ? a : this.ks_get_gcd(b, a % b);
    }

};

Ksdashboardkpiview.props = {
    item: { type: Object, Optional:true},
    dashboard_data: { type: Object, Optional:true},
    ksdatefilter :{type :String, Optional:true},
    pre_defined_filter:{type: Object, Optional:true}
};

Ksdashboardkpiview.template = "Ksdashboardkpiview";
