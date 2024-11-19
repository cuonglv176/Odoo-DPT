/** @odoo-module */

import { registry } from "@web/core/registry";
import {globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions';
import { getCurrency } from "@web/core/currency";
import { formatFloat,formatInteger } from "@web/views/fields/formatters";
import { imageCacheKey } from "@web/views/fields/image/image_field";
import { url } from "@web/core/utils/urls";


const { useEffect, useRef,Component} = owl;

class KsKpiPreview extends Component {
    file_type_magic_word ={'/': 'jpg','R': 'gif','i': 'png','P': 'svg+xml'}

    ks_get_gcd(a, b) {
        return (b == 0) ? a : this.ks_get_gcd(b, a % b);
    }

    _get_rgba_format(val) {
        var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }
    setup() {
        super.setup();
        const self = this;
        this.ks_kpi_ref = useRef("ks_kpi");
        useEffect(() => this.ks_changes());
    }

        ksSum(count_1, count_2, item_info, field, target_1, kpi_data) {
            var self = this;
            var count = count_1 + count_2
            if (field.ks_multiplier_active){
                item_info['count'] = globalfunction._onKsGlobalFormatter(count* field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                item_info['count_tooltip'] = formatFloat(count * field.ks_multiplier, {digits: [0, field.ks_precision_digits]});
            }else{

                item_info['count'] = globalfunction._onKsGlobalFormatter(count, field.ks_data_format, field.ks_precision_digits, field.ks_precision_digits);
                item_info['count_tooltip'] = formatFloat(count, {digits: [0, field.ks_precision_digits]});
            }
            if (field.ks_multiplier_active){
                count = count * field.ks_multiplier;
            }
            var ks_selection = field.ks_unit_selection
            if (ks_selection === 'monetary') {
                var ks_currency_id = field.ks_currency_id[0];
                var ks_data = globalfunction.ks_monetary(item_info['count'], ks_currency_id);
                item_info['count'] = ks_data;
            }else if (ks_selection === 'custom') {
                var ks_field = field.ks_chart_unit;
                item_info['count']= ks_field+" "+item_info['count']
            }
            item_info['target_enable'] = field.ks_goal_enable;
            var ks_color = (target_1 - count) > 0 ? "red" : "green";
            item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
            item_info['ks_comparison'] = true;
            var target_deviation = (target_1 - count) > 0 ? Math.round(((target_1 - count) / target_1) * 100) : Math.round((Math.abs((target_1 - count)) / target_1) * 100);
            if (target_deviation !== Infinity) item_info.target_deviation = formatInteger(target_deviation) + "%";
            else {
                item_info.pre_arrow = false;
                item_info.target_deviation = target_deviation;
            }
            var target_progress_deviation = target_1 == 0 ? 0 : Math.round((count / target_1) * 100);
            item_info.target_progress_deviation = formatInteger(target_progress_deviation) + "%";
            return item_info
        }
        ksPercentage(count_1, count_2, field, item_info, target_1) {
            if (field.ks_multiplier_active){
                count_1 = count_1 * field.ks_multiplier;
                count_2 = count_2 * field.ks_multiplier;
            }
            var count = parseInt((count_1 / count_2) * 100);
            if (field.ks_multiplier_active){
                count = count * field.ks_multiplier;
            }
            if (!count) count = 0;
            item_info['count'] = count ? formatInteger(count) + "%" : "0%";
            item_info['count_tooltip'] = count ? count + "%" : "0%";
            item_info.target_progress_deviation = item_info['count']
            target_1 = target_1 > 100 ? 100 : target_1;
            item_info.target = target_1 + "%";
            item_info.pre_arrow = (target_1 - count) > 0 ? "down" : "up";
            var ks_color = (target_1 - count) > 0 ? "red" : "green";
            item_info['target_enable'] = field.ks_goal_enable;
            item_info['ks_comparison'] = false;
            item_info.target_deviation = item_info.target > 100 ? 100 : item_info.target;
            return item_info;
        }
        get value() {
            var self = this;
            var field = self.props.record.data;
            var kpi_data = JSON.parse(field.ks_kpi_data);
            var count_1 = kpi_data[0].record_data;
            var count_2 = kpi_data[1] ? kpi_data[1].record_data : undefined;
            var target_1 = kpi_data[0].target;
            var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
            var target_view = field.ks_target_view,
            pre_view = field.ks_prev_view;

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
            if (field.ks_previous_period && ks_valid_date_selection.indexOf(field.ks_date_filter_selection) >= 0) {
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
             var target_progress_deviation = String(Math.round((count_1  / target_1) * 100));
             if(field.ks_multiplier_active){
                var target_progress_deviation = String(Math.round(((count_1 * field.ks_multiplier) / target_1) * 100));
             }

            var item_info = {
                count_1: globalfunction.ksNumFormatter(kpi_data[0]['record_data'], 1),
                count_1_tooltip: kpi_data[0]['record_data'],
                count_2: kpi_data[1] ? String(kpi_data[1]['record_data']) : false,
                name: field.name ? field.name : field.ks_model_id[1],
                target_progress_deviation:target_progress_deviation,
                icon_select: field.ks_icon_select,
                default_icon: field.ks_default_icon,
                icon_color: self._get_rgba_format(field.ks_default_icon_color),
                target_deviation: deviation,
                target_arrow: acheive ? 'up' : 'down',
                ks_enable_goal: field.ks_goal_enable,
                ks_previous_period: ks_valid_date_selection.indexOf(field.ks_date_filter_selection) >= 0 ? field.ks_previous_period : false,
                target: globalfunction.ksNumFormatter(target_1, 1),
                previous_period_data: previous_period_data,
                pre_deviation: pre_deviation,
                pre_arrow: pre_acheive ? 'up' : 'down',
                target_view: field.ks_target_view,
                ks_model_id:field.ks_model_id,
                ks_model_id_2: field.ks_model_id_2,
                ks_record_count_type : field.ks_reocrd_count_type,
                ks_dashboard_item_type: field.ks_dashboard_item_type,
                ks_record_field : field.ks_record_field,
                ks_record_field_2 :field.ks_record_field_2,
                ks_rgba_background_color : self._get_rgba_format(field.ks_background_color),
                ks_rgba_font_color : self._get_rgba_format(field.ks_font_color),

            }

            if (item_info.target_deviation === Infinity) item_info.target_arrow = false;
            item_info.target_progress_deviation = parseInt(item_info.target_progress_deviation) ? formatInteger(parseInt(item_info.target_progress_deviation)) : "0"
            if (field.ks_icon) {
                if (!self.isBinSize(field.ks_icon)) {
                    // Use magic-word technique for detecting image type
                    item_info['img_src'] = 'data:image/' + (self.file_type_magic_word[field.ks_icon[0]] || 'png') + ';base64,' + field.ks_icon;
                } else {
                    item_info['img_src'] = url('/web/image', {
                        model: self.env.model.root.resModel,
                        id: JSON.stringify(this.props.record.evalContext.id),
                        field: "ks_icon",
                        // unique forces a reload of the image when the record has been updated
                        unique: imageCacheKey(field.write_date),
                    });
                }
            }
            if (field.ks_multiplier_active){
                item_info['count_1'] = globalfunction._onKsGlobalFormatter(kpi_data[0]['record_data'] * field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                item_info['count_1_tooltip'] = kpi_data[0]['record_data'] * field.ks_multiplier
            }else{
                item_info['count_1'] = globalfunction._onKsGlobalFormatter(kpi_data[0]['record_data'], field.ks_data_format, field.ks_precision_digits);
            }
             if (kpi_data[0].target){
                item_info['target'] = globalfunction._onKsGlobalFormatter(kpi_data[0].target, field.ks_data_format, field.ks_precision_digits);
             }
            if (field.ks_unit){
                if (field.ks_multiplier_active){
                    var ks_record_count = kpi_data[0]['record_data'] * field.ks_multiplier
                }else{
                    var ks_record_count = kpi_data[0]['record_data']
                }
                var ks_selection = field.ks_unit_selection;
                if (ks_selection === 'monetary') {
                    var ks_currency_id = field.ks_currency_id[0];
                    var ks_data = globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                    ks_data = globalfunction.ks_monetary(ks_data, ks_currency_id);
                    item_info['count_1'] = ks_data;
                }else if (ks_selection === 'custom') {
                    var ks_field = field.ks_chart_unit;
                    item_info['count_1']=ks_field+" "+globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                }else {
                    item_info['count_1']= globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                }
            }

            if (kpi_data[1]) {
                switch (field.ks_data_comparison) {
                    case "None":
                         if (field.ks_multiplier_active){
                            var count_tooltip = String(count_1 * field.ks_multiplier) + "/" + String(count_2 * field.ks_multiplier);
                            var count = String(globalfunction.ksNumFormatter(count_1 * field.ks_multiplier, 1)) + "/" + String(globalfunction.ksNumFormatter(count_2 * field.ks_multiplier, 1));
                            var data1 = globalfunction._onKsGlobalFormatter(count_1 * field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                            var data2 = globalfunction._onKsGlobalFormatter(count_2 * field.ks_multiplier, field.ks_data_format, field.ks_precision_digits);
                            if (field.ks_unit){
                                var ks_selection = field.ks_unit_selection;
                                if (ks_selection === 'monetary') {
                                    var ks_currency_id = field.ks_currency_id[0];
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
                                    item_info['count']=String(globalfunction._onKsGlobalFormatter(count_1, field.ks_data_format, field.ks_precision_digits)) + "/" + String(globalfunction._onKsGlobalFormatter(count_2, field.ks_data_format, field.ks_precision_digits));
                                }
                         }else{
                            var count_tooltip = String(count_1) + "/" + String(count_2);
                            var count = String(globalfunction.ksNumFormatter(count_1, 1)) + "/" + String(globalfunction.ksNumFormatter(count_2, 1));
                            var data1 = globalfunction._onKsGlobalFormatter(count_1 , field.ks_data_format, field.ks_precision_digits);
                            var data2 = globalfunction._onKsGlobalFormatter(count_2 , field.ks_data_format, field.ks_precision_digits);
                            if (field.ks_unit){
                                var ks_selection = field.ks_unit_selection;
                                if (ks_selection === 'monetary') {
                                    var ks_currency_id = field.ks_currency_id[0];
                                    data1 = globalfunction.ks_monetary(data1, ks_currency_id);
                                    data2 = globalfunction.ks_monetary(data2, ks_currency_id)
                                    item_info['count'] = data1+"/"+data2;
                                }else{
                                    var ks_field = field.ks_chart_unit;
                                    data1= ks_field+" "+data1
                                    data2= ks_field+" "+data2
                                    item_info['count']= data1+"/"+data2
                                }
                            }else {
                              item_info['count'] = String(globalfunction._onKsGlobalFormatter(count_1, field.ks_data_format, field.ks_precision_digits)) + "/" + String(globalfunction._onKsGlobalFormatter(count_2, field.ks_data_format, field.ks_precision_digits));

                            }
                        }
                        item_info['count_tooltip'] = count_tooltip
                        item_info['target_enable'] = false;
                        break;
                    case "Sum":
                        self.ksSum(count_1, count_2, item_info, field, target_1, kpi_data);
                        break;
                    case "Percentage":
                         self.ksPercentage(count_1, count_2, field, item_info, target_1);
                        break;
                    case "Ratio":
                        var gcd = self.ks_get_gcd(Math.round(count_1), Math.round(count_2));
                        if (field.ks_data_format == 'exact'){
                            if (count_1 && count_2) {
                                item_info['count_tooltip'] = count_1 / gcd + ":" + count_2 / gcd;
                                item_info['count'] = formatFloat(count_1 / gcd, {digits: [0, field.ks_precision_digits]}) + ":" + formatFloat(count_2 / gcd, {digits: [0, field.ks_precision_digits]});
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
                        break;
                }
            }
            return item_info


        }


        ks_changes(){
            var self = this;
            var field =  self.props.record.data;
            var ks_valid_date_selection = ['l_day', 't_week', 't_month', 't_quarter', 't_year'];
            if (field.ks_kpi_data){
                var kpi_data = JSON.parse(field.ks_kpi_data);
                var count_1 = kpi_data[0].record_data;
                var count_2 = kpi_data[1] ? kpi_data[1].record_data : undefined;
                var target_1 = kpi_data[0].target;
                // target deviation //
                if (field.ks_data_comparison === 'Sum'){
                    var count = count_1 + count_2
                    var target_progress_deviation = String(Math.round((count / target_1) * 100))
                }else if (field.ks_data_comparison === 'Percentage'){
                    var count = parseInt((count_1 / count_2) * 100)
                    var target_progress_deviation = String(Math.round((count / target_1) * 100))
                }
                else{
                    var target_progress_deviation = String(Math.round((count_1  / target_1) * 100));
                }
                if(field.ks_multiplier_active && (field.ks_data_comparison === 'Percentage' || field.ks_data_comparison === 'Sum')){
                    var target_progress_deviation = String(Math.round(((count * field.ks_multiplier) / target_1) * 100));
                }else if (field.ks_multiplier_active){
                    var target_progress_deviation = String(Math.round(((count_1 * field.ks_multiplier) / target_1) * 100));
                }
                // goal enable color //
                if (field.ks_goal_enable) {
                    var diffrence = 0.0
                    if (field.ks_data_comparison === 'Sum'){
                        var count = count_1 + count_2
                        var diffrence = count - target_1
                    }else if (field.ks_data_comparison === 'Percentage'){
                        var count = parseInt((count_1 / count_2) * 100)
                        var diffrence = count - target_1
                    }
                    else{
                        var diffrence = count - target_1
                    }
                    if(field.ks_multiplier_active && (field.ks_data_comparison === 'Percentage' || field.ks_data_comparison === 'Sum')){
                        var  diffrence = (count_1 * field.ks_multiplier) - target_1
                    }else if (field.ks_multiplier_active){
                        var diffrence = count_1 - target_1
                    }

                    var acheive = diffrence >= 0 ? true : false;
                    if (acheive) {
                        $(this.ks_kpi_ref.el).find(".target_deviation").css({
                            "color": "green",
                        });
                    } else {
                        $(this.ks_kpi_ref.el).find(".target_deviation").css({
                            "color": "red",
                        });
                    }
                }
                if ($(this.ks_kpi_ref.el).find('.row').children().length !== 2) {
                    $(this.ks_kpi_ref.el).find('.row').children().addClass('text-center');
                }
                if (field.ks_previous_period && ks_valid_date_selection.indexOf(field.ks_date_filter_selection) >= 0) {
                    var previous_period_data = kpi_data[0].previous_period;
                    var pre_diffrence = (count_1 - previous_period_data);
                    if (field.ks_multiplier_active){
                        var previous_period_data = kpi_data[0].previous_period * field.ks_multiplier;
                        var pre_diffrence = (count_1 * field.ks_multiplier   - previous_period_data);
                    }
                    var pre_acheive = pre_diffrence > 0 ? true : false;
                    if (pre_acheive) {
                        $(this.ks_kpi_ref.el).find(".pre_deviation").css({
                           "color": "green",
                        });
                    } else {
                        $(this.ks_kpi_ref.el).find(".pre_deviation").css({
                            "color": "red",
                        });
                    }
                }
                if (field.ks_target_view === "Progress Bar" && field.ks_goal_enable && field.ks_standard_goal_value){
                    $(this.ks_kpi_ref.el).find('#ks_progressbar').val(parseInt(target_progress_deviation));
                }

            }

        }
        ks_get_gcd(a, b) {
            return (b == 0) ? a : this.ks_get_gcd(b, a % b);
        }
        _get_rgba_format(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }
        isBinSize(value) {
            return /^\d+(\.\d*)? [^0-9]+$/.test(value);
        }

    }

KsKpiPreview.template = "ks_kpi";
export const KsKpiPreviewfield = {
    component :KsKpiPreview,
}
registry.category("fields").add("ks_dashboard_kpi_owlpreview",KsKpiPreviewfield);
