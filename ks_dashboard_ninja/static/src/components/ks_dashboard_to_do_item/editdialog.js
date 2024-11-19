/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { Component,useRef } from "@odoo/owl";

export class Todoeditdialog extends Component {
    setup() {
    }
    _ks_click(ev){
        this.props.confirm(event)
        this.props.close()
    }
}
Todoeditdialog.template = "Kseditdialog";
Todoeditdialog.props = {
    close: Function,
    confirm: { type: Function, optional: true },
    ks_description: { type: String, optional: true },
}
Todoeditdialog.components = { Dialog };

export class addtododialog extends Component{
    setup(){
    }
    ks_task_click(ev){
        this.props.confirm(event)
        this.props.close()
    }
}
addtododialog.template = "Ksaddtaskdialog";
addtododialog.props = {
    close: Function,
    confirm: { type: Function, optional: true },
}
addtododialog.components = { Dialog };
