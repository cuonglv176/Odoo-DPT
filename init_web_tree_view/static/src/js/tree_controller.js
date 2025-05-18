/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TreeController extends Component {
    setup() {
        this.actionService = useService("action");
        this.domain = this.props.domain || [];
        this.context = this.props.context || {};
    }
}

TreeController.template = "init_web_tree_view.TreeController";
TreeController.props = {
    model: Object,
    resModel: String,
    actionId: { type: Number, optional: true },
    context: { type: Object, optional: true },
    domain: { type: Array, optional: true },
};