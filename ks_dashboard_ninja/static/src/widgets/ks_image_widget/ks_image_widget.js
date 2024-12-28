/** @odoo-module */

import { formatDate, parseDateTime } from "@web/core/l10n/dates";
import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Ksiconselectordialog } from "@ks_dashboard_ninja/widgets/ks_image_widget/ks_icon_selector_dialog"

const { Component,useEffect, useRef, xml, onWillUpdateProps,onMounted,onWillStart} = owl;

export class KsImageWidget extends  Component {

    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }

     ks_image_widget_icon_container(ev){
         var self = this;
         var ks_result = this.dialogService.add(Ksiconselectordialog,{
         ks_icon_set :['home', 'puzzle-piece', 'clock-o', 'comments-o', 'car', 'calendar', 'calendar-times-o', 'bar-chart', 'commenting-o', 'star-half-o', 'address-book-o', 'tachometer', 'search', 'money', 'line-chart', 'area-chart', 'pie-chart', 'check-square-o', 'users', 'shopping-cart', 'truck', 'user-circle-o', 'user-plus', 'sun-o', 'paper-plane', 'rss', 'gears', 'check', 'book'],
         confirm: async (info) => {
                await this.props.record.update({ [this.props.name]: info});

         },
            });
     }

     ks_remove_icon(ev){
       var ks_self = this;
       this.props.record.update({ [this.props.name]: ""});
    }

}
KsImageWidget.template="image_widget";
export const ksImageWidgetField = {
    component:  KsImageWidget
};
registry.category("fields").add("ks_image_widget",ksImageWidgetField);

