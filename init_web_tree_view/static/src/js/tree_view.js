/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardViewProps } from "@web/views/standard_view_props";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { Layout } from "@web/search/layout";

class TreeModel {
    constructor(env, params) {
        this.env = env;
        this.orm = env.services.orm;
        this.resModel = params.resModel;
        this.fields = params.fields;
        this.archInfo = params.archInfo;
        this.domain = params.domain || [];
        this.context = params.context || {};
        this.childField = params.childField;
        this.data = { records: [] };
    }

    async load() {
        const domain = [['parent_id', '=', false], ...this.domain];
        try {
            const records = await this.orm.searchRead(
                this.resModel,
                domain,
                [],
                { context: this.context }
            );
            this.data.records = records;
            return this.data;
        } catch (error) {
            console.error("Error fetching tree data:", error);
            return { records: [] };
        }
    }

    async loadChildren(parentId) {
        const domain = [['parent_id', '=', parentId], ...this.domain];
        try {
            const records = await this.orm.searchRead(
                this.resModel,
                domain,
                [],
                { context: this.context }
            );
            return records;
        } catch (error) {
            console.error("Error fetching children:", error);
            return [];
        }
    }
}

class TreeRenderer extends Component {
    static template = "init_web_tree_view.TreeRenderer";
    static props = {
        records: { type: Array, optional: true },
        fields: Object,
        childField: { type: String, optional: true },
        model: String,
        arch: Object,
        context: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            expandedRows: {},
            loading: {},
        });
    }

    async toggleNode(recordId) {
        if (this.state.expandedRows[recordId]) {
            // Collapse
            this.state.expandedRows[recordId] = false;
        } else {
            // Expand
            this.state.expandedRows[recordId] = true;
            this.state.loading[recordId] = true;

            try {
                // Load children if not already loaded
                await this.props.onLoadChildren(recordId);
            } finally {
                this.state.loading[recordId] = false;
            }
        }
    }

    isExpanded(recordId) {
        return this.state.expandedRows[recordId] || false;
    }

    isLoading(recordId) {
        return this.state.loading[recordId] || false;
    }

    getLevel(record) {
        return record._level || 0;
    }

    getPadding(level) {
        return { paddingLeft: `${(level || 0) * 20 + 5}px` };
    }

    hasChildren(record) {
        return record.child_ids && record.child_ids.length > 0;
    }

    onRowClick(record) {
        if (this.hasChildren(record)) {
            this.toggleNode(record.id);
        } else {
            // Open form view for leaf nodes
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: this.props.model,
                res_id: record.id,
                views: [[false, 'form']],
                target: 'current',
            });
        }
    }
}

export class InitTreeView extends Component {
    static template = "init_web_tree_view.TreeView";
    static components = { Layout, TreeRenderer };
    static props = {
        ...standardViewProps,
    };
    static type = "init_tree";
    static display_name = _t("Hierarchy Tree View");
    static icon = "fa-align-left";
    static multiRecord = true;

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        const childField = this.props.arch.attrs.childField;

        this.state = useState({
            records: [],
            loading: true,
        });

        this.model = new TreeModel(this.env, {
            resModel: this.props.resModel,
            fields: this.props.fields,
            archInfo: this.props.archInfo,
            domain: this.props.domain || [],
            context: this.props.context || {},
            childField: childField,
        });

        onWillStart(async () => {
            const data = await this.model.load();
            this.state.records = data.records.map(record => ({...record, _level: 0}));
            this.state.loading = false;
        });
    }

    async loadChildren(parentId) {
        const children = await this.model.loadChildren(parentId);
        const parentIndex = this.state.records.findIndex(r => r.id === parentId);

        if (parentIndex !== -1) {
            const parentLevel = this.state.records[parentIndex]._level || 0;
            const childrenWithLevel = children.map(child => ({
                ...child,
                _level: parentLevel + 1,
            }));

            // Insert children after parent
            this.state.records.splice(parentIndex + 1, 0, ...childrenWithLevel);
        }

        return children;
    }
}

registry.category("views").add("init_tree", InitTreeView);