/** @odoo-module */

import { registry } from "@web/core/registry";
import {globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions';
import { getCurrency } from "@web/core/currency";
import { formatFloat,formatInteger } from "@web/views/fields/formatters";
import { imageCacheKey } from "@web/views/fields/image/image_field";
import { url } from "@web/core/utils/urls";

const { useEffect, useRef, xml, onWillUpdateProps,Component} = owl;

class KsItemPreview extends Component {

        file_type_magic_word= {'/': 'jpg','R': 'gif','i': 'png','P': 'svg+xml'}

        setup() {
            super.setup();
            const self = this;
        }
        get value(){
            var self = this;
            var field = self.props.record.data;
            var item_info;
            var ks_rgba_background_color, ks_rgba_font_color, ks_rgba_icon_color;
            ks_rgba_background_color = self._get_rgba_format(field.ks_background_color)
            ks_rgba_font_color = self._get_rgba_format(field.ks_font_color)
            ks_rgba_icon_color = self._get_rgba_format(field.ks_default_icon_color)
            item_info = {
                name: field.name,
                count: globalfunction.ksNumFormatter(field.ks_record_count, 1),
                icon_select: field.ks_icon_select,
                default_icon: field.ks_default_icon,
                icon_color: ks_rgba_icon_color,
                count_tooltip: formatFloat(field.ks_record_count, {digits: [0, field.ks_precision_digits]}),
                ks_layout : field.ks_layout,
                ks_rgba_background_color : self._get_rgba_format(field.ks_background_color),
                ks_rgba_font_color : self._get_rgba_format(field.ks_font_color),
                ks_rgba_icon_color : self._get_rgba_format(field.ks_default_icon_color),
                ks_rgba_dark_background_color_l2 : self._get_rgba_format(self.ks_get_dark_color(field.ks_background_color.split(',')[0], field.ks_background_color.split(',')[1], -10))
            }

            if (field.ks_icon) {
                if (!self.isBinSize(field.ks_icon)) {
                    // Use magic-word technique for detecting image type
                    item_info['img_src'] = 'data:image/' + (self.file_type_magic_word[field.ks_icon] || 'png') + ';base64,' + field.ks_icon;
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
            if (!field.name) {
                if (field.ks_model_name) {
                    item_info['name'] = field.ks_model_id[1];
                } else {
                    item_info['name'] = "Name";
                }
            }

            if (field.ks_multiplier_active){
                var ks_record_count = field.ks_record_count * field.ks_multiplier
                item_info['count'] = globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                item_info['count_tooltip'] = ks_record_count;
            }else{
                item_info['count'] = globalfunction._onKsGlobalFormatter(field.ks_record_count, field.ks_data_format, field.ks_precision_digits);
            }

            if (field.ks_unit){
                if (field.ks_multiplier_active){
                    var ks_record_count = field.ks_record_count * field.ks_multiplier
                }else{
                    var ks_record_count = field.ks_record_count
                }
                var ks_selection = field.ks_unit_selection;
                if (ks_selection === 'monetary') {
                    var ks_currency_id = field.ks_currency_id[0];
                    var ks_data = globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                    ks_data = globalfunction.ks_monetary(ks_data, ks_currency_id);
                    item_info['count'] = ks_data;
                } else if (ks_selection === 'custom') {
                    var ks_field = field.ks_chart_unit;
                    item_info['count']= ks_field+" "+globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                }else {
                    item_info['count']= globalfunction._onKsGlobalFormatter(ks_record_count, field.ks_data_format, field.ks_precision_digits);
                }
            }
            return item_info
        }

        isBinSize(value) {
            return /^\d+(\.\d*)? [^0-9]+$/.test(value);
        }
        _get_rgba_format(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }
         ks_get_dark_color(color, opacity, percent) {
            var num = parseInt(color.slice(1), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
        }
 }

 KsItemPreview.template = "ks_tile";
 export const KsItemPreviewfield = {
    component :KsItemPreview,
 }
 registry.category("fields").add('ks_dashboard_item_preview_owl', KsItemPreviewfield);

