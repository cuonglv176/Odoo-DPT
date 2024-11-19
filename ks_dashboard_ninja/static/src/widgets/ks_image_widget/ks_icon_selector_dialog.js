/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { Component,useRef } from "@odoo/owl";

export class Ksiconselectordialog extends Component {
    setup() {
    this.ks_modal = useRef("ks_modal")
    this.ks_search = useRef("ks_search")
    this.ksSelectedIcon = false
    }

    ks_icon_container_list(e){
        var self = this;
        (this.ks_modal.el.querySelectorAll('.ks_icon_container_list')).forEach((selected_icon) => {
            $(selected_icon).removeClass('ks_icon_selected');
        });
        $(e.currentTarget).addClass('ks_icon_selected')
        $(".ks_icon_container_open_button").removeClass("d-none")
       self.ksSelectedIcon = $(e.currentTarget).find('span').attr('id').split('.')[1]
    }

     ks_fa_icon_search(e) {
        var self = this
        if(this.ks_search.el.querySelectorAll('.ks_fa_search_icon').length > 0){
            this.ks_search.el.querySelectorAll('.ks_fa_search_icon').forEach(function(el){
                el.remove();
            })
        }
        var ks_fa_icon_name = this.ks_search.el.querySelectorAll('.ks_modal_icon_input')[0].value;
        if (ks_fa_icon_name.slice(0, 3) === "fa-") {
            ks_fa_icon_name = ks_fa_icon_name.slice(3)
        }
        var ks_fa_icon_render = $('<div>').addClass('ks_icon_container_list ks_fa_search_icon')
        $('<span>').attr('id', 'ks.' + ks_fa_icon_name.toLocaleLowerCase()).addClass("fa fa-" + ks_fa_icon_name.toLocaleLowerCase() + " fa-4x").appendTo($(ks_fa_icon_render))
        $(ks_fa_icon_render).appendTo(this.ks_modal.el)
        this.ks_modal.el.querySelectorAll('.ks_fa_search_icon').forEach((item) =>{
            item.addEventListener('click', this.ks_icon_container_list.bind(this))
        })
     }


    async _ks_icon_container_open_button(e){
        try {
            await this.props.confirm(this.ksSelectedIcon);
        } catch (e) {
            this.props.close();
        }
        this.props.close();
    }
}
Ksiconselectordialog.template = "Ksicondialog";
Ksiconselectordialog.props = {
    close: Function,
    confirm: { type: Function, optional: true },
    ks_icon_set: { type: Object, optional: true },
}
Ksiconselectordialog.components = { Dialog };
