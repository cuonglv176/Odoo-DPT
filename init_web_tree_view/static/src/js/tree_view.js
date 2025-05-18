/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardViewProps } from "@web/views/standard_view_props";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";
import { TreeModel } from "./tree_model";
import { TreeRenderer } from "./tree_renderer";
import { TreeController } from "./tree_controller";
import { Layout } from "@web/search/layout";

export class InitTreeView extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.init_tree = false;

        const { arch, fields, resModel } = this.props;
        const attrs = arch.attrs || {};

        this.model = new TreeModel(this.env, {
            resModel: resModel,
            fields: fields,
            archInfo: this.props.archInfo,
            domain: this.props.domain || [],
            context: this.props.context || {},
        });

        this.controller = new TreeController(this.env, {
            model: this.model,
            resModel: resModel,
            actionId: this.props.actionId,
            context: this.props.context || {},
            domain: this.props.domain || [],
        });

        this.renderer = new TreeRenderer(this.env, {
            fields: fields,
            children_field: this.props.archInfo.fieldParent,
            model: resModel,
            arch: arch,
            context: this.props.context || {},
            action: this.props.action,
        });

        onWillStart(async () => {
            await this.model.load();
        });
    }
}

InitTreeView.template = "init_web_tree_view.TreeView";
InitTreeView.components = { Layout };
InitTreeView.props = {
    ...standardViewProps,
};

InitTreeView.type = "init_tree";
InitTreeView.display_name = _t("INIT Tree View");
InitTreeView.icon = "fa-align-left";
InitTreeView.searchable = false;
InitTreeView.withSearchBar = false;
InitTreeView.withControlPanel = true;
InitTreeView.withSearchPanel = false;
InitTreeView.multiRecord = true;

registry.category("views").add("init_tree", InitTreeView);