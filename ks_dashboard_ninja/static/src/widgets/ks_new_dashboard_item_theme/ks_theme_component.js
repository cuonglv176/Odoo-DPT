/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component} = owl;

export class KsDashboardTheme extends Component {
    setup(){
        var self = this.props;
        this.props.colors = ['white','blue','red','yellow','green']
    }
    get value(){
        return this.props.record.data[this.props.name]
    }

    ks_dashboard_theme_input_container_click(ev) {
        var self = this.props;
        var $box = $(ev.currentTarget).find(':input');
        if ($box.is(":checked")) {
            $('.ks_dashboard_theme_input').prop('checked', false)
            $box.prop("checked", true);
        } else {
            $box.prop("checked", false);
        }
        this.props.record.update({ [this.props.name]: $box[0].value });
        }
    }
KsDashboardTheme.template="Ks_theme";
export const KsDashboardThemeField = {
    component:  KsDashboardTheme,
    supportedTypes: ["char"],
};

registry.category("fields").add('ks_dashboard_item_theme', KsDashboardThemeField);

