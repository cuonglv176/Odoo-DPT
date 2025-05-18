/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { formatters } from "@web/views/fields/formatters";

export class TreeRenderer extends Component {
    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");

        this.rootRef = useRef("root");
        this.records = {};

        onMounted(() => {
            this._setupColors();
            this._hookRowClick();
            this._fetchInitialData();
        });
    }

    async _fetchInitialData() {
        const domain = [['parent_id', '=', false]];
        try {
            const records = await this.orm.searchRead(
                this.props.model,
                domain,
                [],
                { context: this.props.context || {} }
            );

            records.forEach(record => {
                this.records[record.id] = record;
            });

            this._renderRows(null, records);
        } catch (error) {
            console.error("Error fetching tree data:", error);
        }
    }

    _setupColors() {
        if (this.props.arch.attrs && this.props.arch.attrs.colors) {
            this.colors = this.props.arch.attrs.colors.split(';')
                .filter(colorPair => colorPair)
                .map(colorPair => {
                    const [color, expr] = colorPair.split(':');
                    return [color, expr];
                });
        } else {
            this.colors = [];
        }
    }

    _hookRowClick() {
        if (!this.rootRef.el) return;

        // Handle row clicks and expand/collapse functionality
        // This will be implemented with DOM manipulation since we're
        // not using reactive state for the tree rows
    }

    _renderRows(parentId, records) {
        if (!this.rootRef.el) return;

        const tbody = this.rootRef.el.querySelector('tbody');
        if (!tbody) return;

        const fragment = document.createDocumentFragment();
        const level = parentId ? parseInt(document.getElementById(`treerow_${parentId}`)?.dataset.level || 0, 10) + 1 : 0;

        records.forEach(record => {
            const tr = document.createElement('tr');
            tr.id = `treerow_${record.id}`;
            tr.dataset.id = record.id;
            tr.dataset.level = level;
            tr.dataset.rowParentId = parentId || '';

            const hasChildren = record[this.props.children_field] && record[this.props.children_field].length > 0;
            const className = hasChildren ? 'treeview-tr' : 'treeview-td';

            this.props.arch.children.forEach(field => {
                const td = document.createElement('td');
                td.dataset.id = record.id;
                td.className = className;

                const style = `background-position: ${19 * level}px; padding-left: ${4 + 19 * level}px;`;
                td.setAttribute('style', style);

                const span = document.createElement('span');
                const fieldName = field.attrs.name;
                const fieldDef = this.props.fields[fieldName];

                if (fieldDef && record[fieldName] !== undefined) {
                    const formatter = formatters[fieldDef.type] || (val => val !== undefined ? String(val) : "");
                    span.textContent = formatter(record[fieldName], fieldDef);
                }

                td.appendChild(span);
                tr.appendChild(td);
            });

            fragment.appendChild(tr);
        });

        if (parentId) {
            const parentRow = document.getElementById(`treerow_${parentId}`);
            if (parentRow) {
                parentRow.after(fragment);
            }
        } else {
            tbody.appendChild(fragment);
        }

        this._hookRowClick();
    }
}

TreeRenderer.template = "init_web_tree_view.TreeRenderer";
TreeRenderer.props = {
    fields: Object,
    children_field: { type: String, optional: true },
    model: String,
    arch: Object,
    context: { type: Object, optional: true },
    action: { type: Object, optional: true },
};