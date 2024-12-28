/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component,useState,onWillUpdateProps} = owl;

export class KsColorPicker extends Component{
        setup(){
            var self=this.props;
        }
        get value(){
            return{
                'ks_color':this.props.record.data[this.props.name].split(",")[0] || "#376CAE",
                'ks_opacity':this.props.record.data[this.props.name].split(",")[1] ||'0.99'
            }
        }

        _ksOnColorChange(ev) {
            var new_value=(ev.currentTarget.value.concat("," + this.props.record.data[this.props.name].split(',')[1]));
            this.props.record.update({ [this.props.name]: new_value });

        }

        _ksOnOpacityChange(ev) {
            var new_value=(this.props.record.data[this.props.name].split(',')[0].concat("," + event.currentTarget.value));
            this.props.record.update({ [this.props.name]: new_value });
        }

        _ksOnOpacityInput(ev) {
            var self = this;
            var color;
            if (this.props.name == "ks_background_color") {
                color = $('.ks_db_item_preview_color_picker').css("background-color")
                $('.ks_db_item_preview_color_picker').css("background-color", self.get_color_opacity_value(color, event.currentTarget.value))

                color = $('.ks_db_item_preview_l2').css("background-color")
                $('.ks_db_item_preview_l2').css("background-color", self.get_color_opacity_value(color, event.currentTarget.value))

            } else if (this.props.name == "ks_default_icon_color") {
                color = $('.ks_dashboard_icon_color_picker > span').css('color')
                $('.ks_dashboard_icon_color_picker > span').css('color', self.get_color_opacity_value(color, event.currentTarget.value))
            } else if (this.props.name == "ks_font_color") {
                color = $('.ks_db_item_preview').css("color")
                color = $('.ks_db_item_preview').css("color", self.get_color_opacity_value(color, event.currentTarget.value))
            }
        }

        get_color_opacity_value(color, val) {
            if (color) {
                return color.replace(color.split(',')[3], val + ")");
            } else {
                return false;
            }
        }


 }
 KsColorPicker.template="Ks_color_picker_opacity_view";
 KsColorPicker.props = {
    ...standardFieldProps,
};
export const ksColorPickerField = {
    component:  KsColorPicker,
    supportedTypes: ["char"],
};
 registry.category("fields").add('Ks_dashboard_color_picker_owl', ksColorPickerField);
