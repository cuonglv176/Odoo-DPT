/** @odoo-module **/
import { Component, useState ,useEffect,onWillUpdateProps,useRef} from "@odoo/owl";
import {globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions';
import { loadBundle } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

export class Ksdashboardtile extends Component{
    setup(){
        var self = this;
        this._rpc = useService("rpc");
        this.actionService = useService("action");
        this.ks_container_class = 'grid-stack-item';
        this.ks_inner_container_class = 'grid-stack-item-content';
        this.state = useState({data_count:""})
        this.item = this.props.item
        this.ks_dashboard_data = this.props.dashboard_data
        this.prepare_item();
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
            return jsonrpc("/web/dataset/call_kw/",{
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
                this.prepare_item()
            }.bind(this));
        }




    ksStopClickPropagation(e){
        this.ksAllowItemClick = false;
    }

    prepare_item() {
        var self = this;
        var ks_icon_url, item_view;
        var ks_rgba_background_color, ks_rgba_font_color, ks_rgba_default_icon_color,ks_rgba_button_color;
        var style_main_body, style_image_body_l2, style_domain_count_body, style_button_customize_body, style_button_delete_body;
        if (this.item.ks_multiplier_active){
            var ks_record_count = this.item.ks_record_count * this.item.ks_multiplier
            if (this.item.ks_unit){
                var ks_selection = this.item.ks_unit_selection;
                if (ks_selection === 'monetary') {
                    var ks_currency_id = this.item.ks_currency_id;
                    var ks_data = globalfunction._onKsGlobalFormatter(ks_record_count, this.item.ks_data_formatting, this.item.ks_precision_digits);
                    ks_data = globalfunction.ks_monetary(ks_data, ks_currency_id);
                    var data_count = ks_data;
                } else{
                    var ks_field = this.item.ks_chart_unit;
                    var data_count= ks_field+" "+globalfunction._onKsGlobalFormatter(ks_record_count, this.item.ks_data_formatting, this.item.ks_precision_digits);
                }
            }else {
                var data_count= globalfunction._onKsGlobalFormatter(ks_record_count, this.item.ks_data_formatting, this.item.ks_precision_digits);
            }
            var count = ks_record_count;
        }else{
            var ks_record_count = this.item.ks_record_count
            if (this.item.ks_unit){
                var ks_selection = this.item.ks_unit_selection;
                if (ks_selection === 'monetary') {
                    var ks_currency_id = this.item.ks_currency_id;
                    var ks_data = globalfunction._onKsGlobalFormatter(ks_record_count, this.item.ks_data_formatting, this.item.ks_precision_digits);
                    ks_data = globalfunction.ks_monetary(ks_data, ks_currency_id);
                    var data_count = ks_data;
                } else{
                    var ks_field = this.item.ks_chart_unit;
                    var data_count= ks_field+" "+globalfunction._onKsGlobalFormatter(ks_record_count, this.item.ks_data_formatting, this.item.ks_precision_digits);
                }
            }else {
                var data_count= globalfunction._onKsGlobalFormatter(ks_record_count, this.item.ks_data_formatting, this.item.ks_precision_digits);
            }
            var count = ks_record_count;
        }
        if (this.item.ks_icon_select == "Custom") {
            if (this.item.ks_icon[0]) {
                ks_icon_url = 'data:image/' + (self.file_type_magic_word[this.item.ks_icon[0]] || 'png') + ';base64,' + this.item.ks_icon;
            } else {
                ks_icon_url = false;
            }
        }

        this.item.ksIsDashboardManager = self.ks_dashboard_data.ks_dashboard_manager;
        this.item.ksIsUser = true;
//        if (this.item.ks_tv_play){
//            this.item.ksIsUser = false;
//        }
        ks_rgba_background_color = self._ks_get_rgba_format(this.item.ks_background_color);
        ks_rgba_font_color = self._ks_get_rgba_format(this.item.ks_font_color);
        this.ks_rgba_default_icon_color = self._ks_get_rgba_format(this.item.ks_default_icon_color);
        this.ks_rgba_button_color = self._ks_get_rgba_format(this.item.ks_button_color);
        if (this.item.ks_info){
            var ks_description = this.item.ks_info.split('\n');
            var ks_description = ks_description.filter(element => element !== '')
        }else {
            var ks_description = false;
        }
        this.ks_icon_url = ks_icon_url
        this.state.data_count = data_count
        this.count = count
        this.ks_info = ks_description
        this.ks_dashboard_list= self.ks_dashboard_data.ks_dashboard_list
        this.style_main_body = this._ksMainBodyStyle(ks_rgba_background_color, ks_rgba_font_color, this.item).background_style;
    }

    get style_image_body_l2(){
        return this._ksMainBodyStyle(this.ks_rgba_background_color, this.ks_rgba_font_color, this.item).style_image_body_l2;
    }

    get style_main_body_l4(){
        return "color : " + this.ks_rgba_font_color + ";border : solid;border-width : 1px;";
    }

    get style_image_body_l4(){
        return this._ksMainBodyStyle(this.ks_rgba_background_color, this.ks_rgba_font_color, this.item).background_style;
    }

    _ks_get_rgba_format(val){
        var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
        }).join(",");
        return "rgba(" + rgba + "," + val.split(',')[1] + ")";
    }

    _ksMainBodyStyle(ks_rgba_background_color, ks_rgba_font_color, tile){
        var background_style = "background-color:" + ks_rgba_background_color + ";color : " + ks_rgba_font_color + ";";
        var ks_rgba_dark_background_color_l2 = this._ks_get_rgba_format(this.ks_get_dark_color(tile.ks_background_color.split(',')[0], tile.ks_background_color.split(',')[1], -10));
        var style_image_body_l2 = "background-color:" + ks_rgba_dark_background_color_l2 + ";";
        return {
            'background_style': background_style,
            'style_image_body_l2': style_image_body_l2
        };
    }

    ks_get_dark_color(color, opacity, percent) {
        var num = parseInt(color.slice(1), 16),
            amt = Math.round(2.55 * percent),
            R = (num >> 16) + amt,
            G = (num >> 8 & 0x00FF) + amt,
            B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
    }


};

Ksdashboardtile.props = {
    item: { type: Object, Optional:true},
    dashboard_data: { type: Object, Optional:true},
    ksdatefilter : {type:String,Optional:true},
    pre_defined_filter :{type:Object, Optional:true}
};

Ksdashboardtile.template = "ksdashboardtile";
