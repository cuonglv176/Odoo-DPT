/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";

const { useEffect, useRef, onWillStart ,Component } = owl;

class KsToDOViewPreview extends Component {
    setup() {
        super.setup();
        const self = this;
    }


    _ks_get_rgba_format(val) {
        var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
        }).join(",");
        return "rgba(" + rgba + "," + val.split(',')[1] + ")";
    }

    get value() {
        const self = this;
        var rec = self.props.record.data;
        if (rec.ks_dashboard_item_type === 'ks_to_do') {
            var ks_header_color = self._ks_get_rgba_format(rec.ks_header_bg_color);
            var ks_font_color = self._ks_get_rgba_format(rec.ks_font_color);
            var ks_rgba_button_color = self._ks_get_rgba_format(rec.ks_button_color);
            var list_to_do_data = {}
            if (rec.ks_to_do_data){
                list_to_do_data = JSON.parse(rec.ks_to_do_data)
            }

                var item_info ={
                    ks_to_do_view_name: rec.name ? rec.name : 'Name',
                    to_do_view_data: list_to_do_data,
                    ks_header_color : ks_header_color,
                    ks_font_color :ks_font_color

                }
//            $todoViewContainer.find('.ks_card_header').addClass('ks_bg_to_color').css({"background-color": ks_header_color });
//            $todoViewContainer.find('.ks_card_header').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
//            $todoViewContainer.find('.ks_li_tab').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
//            $todoViewContainer.find('.ks_chart_heading').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
//            $(this.input.el.parentElement).append($todoViewContainer);
        }
        return item_info
    }
    ksOnToDoClick(ev){
            ev.preventDefault();
            var self= this;
            var tab_id = $(ev.target).attr('href');
            var $tab_section = $('#' + tab_id.substring(1));
            $(ev.target).addClass("active");
            $(ev.target).parent().siblings().each(function(){
                $(this).children().removeClass("active");
            });
            $('#' + tab_id.substring(1)).siblings().each(function(){
                $(this).removeClass("active");
                $(this).addClass("fade");
            });
            $tab_section.removeClass("fade");
            $tab_section.addClass("active");
            $(ev.target).parent().parent().siblings().attr('data-section-id', $(ev.target).data().sectionId);
        }
}
KsToDOViewPreview.template="ks_to_do_container";
export const KsToDOViewPreviewfield = {
    component:KsToDOViewPreview
}
registry.category("fields").add("ks_dashboard_to_do_preview", KsToDOViewPreviewfield);

