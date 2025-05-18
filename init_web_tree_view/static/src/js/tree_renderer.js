/** @odoo-module **/

import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { formatters } from "@web/views/fields/formatters";
import { evaluateExpr } from "@web/core/py_js/py";

export class TreeRenderer extends Component {
    setup() {
        this.state = useState({
            records: {},
        });

        this.actionService = useService("action");
        this.orm = useService("orm");

        this.rootRef = useRef("root");
        this.modelName = this.props.model;
        this.fields = this.props.fields;
        this.arch = this.props.arch;
        this.children_field = this.props.children_field || 'child_ids';
        this.records = {};
        this.action = this.props.action;

        onMounted(() => {
            this._setupColors();
            this._hookRowClick();
        });
    }

    _setupColors() {
        if (this.arch.attrs && this.arch.attrs.colors) {
            this.colors = this.arch.attrs.colors.split(';')
                .filter(colorPair => colorPair)
                .map(colorPair => {
                    const [color, expr] = colorPair.split(':');
                    return [color, expr];
                });
        } else {
            this.colors = [];
        }
    }

    colorFor(record) {
        if (!this.colors || !this.colors.length) {
            return '';
        }

        for (const [color, expr] of this.colors) {
            if (evaluateExpr(expr, record)) {
                return `color: ${color};`;
            }
        }
        return '';
    }

    _hookRowClick() {
        if (!this.rootRef.el) return;

        // Handle row clicks
        this.rootRef.el.querySelectorAll('.treeview-td span, .treeview-tr span').forEach(span => {
            span.addEventListener('click', (e) => {
                e.stopImmediatePropagation();
                const id = parseInt(e.currentTarget.closest('tr').dataset.id, 10);
                this.activate(id);
            });
        });

        // Handle expand/collapse
        this.rootRef.el.querySelectorAll('.treeview-tr').forEach(row => {
            row.addEventListener('click', (e) => {
                const recordId = parseInt(e.currentTarget.dataset.id, 10);
                const rowParentId = e.currentTarget.dataset.rowParentId;
                const record = this.records[recordId];

                if (!record) return;

                const childrenIds = record[this.children_field] || [];
                let isLoaded = 0;

                childrenIds.forEach(childId => {
                    const childRow = this.rootRef.el.querySelector(`[id=treerow_${childId}][data-row-parent-id="${recordId}"]`);
                    if (childRow) {
                        if (childRow.style.display === 'none') {
                            isLoaded = -1;
                        } else {
                            isLoaded++;
                        }
                    }
                });

                if (isLoaded === 0) {
                    if (!e.currentTarget.parentElement.classList.contains('o_open')) {
                        this.getdata(recordId, childrenIds);
                    }
                } else {
                    this.showcontent(e.currentTarget, recordId, isLoaded < 0);
                }
            });
        });
    }

    async getdata(id, childrenIds) {
        try {
            const fields = this.fieldsList();
            const records = await this.orm.read(this.modelName, childrenIds, fields);

            records.forEach(record => {
                this.records[record.id] = record;
            });

            const currNode = this.rootRef.el.querySelector(`#treerow_${id}`);
            const level = currNode ? parseInt(currNode.dataset.level || 0, 10) : 0;

            // Create new rows for children
            const fragment = document.createDocumentFragment();
            records.forEach(record => {
                const tr = document.createElement('tr');
                tr.id = `treerow_${record.id}`;
                tr.dataset.id = record.id;
                tr.dataset.level = level + 1;
                tr.dataset.rowParentId = id;

                const hasChildren = record[this.children_field] && record[this.children_field].length > 0;
                const className = hasChildren ? 'treeview-tr' : 'treeview-td';

                this.arch.children.forEach(field => {
                    const td = document.createElement('td');
                    td.dataset.id = record.id;
                    td.className = className;

                    const style = `background-position: ${19 * level}px; padding-left: ${4 + 19 * level}px; ${this.colorFor(record)}`;
                    td.setAttribute('style', style);

                    const span = document.createElement('span');
                    const fieldName = field.attrs.name;
                    const fieldDef = this.fields[fieldName];

                    if (fieldDef.type === 'boolean' && record[fieldName] === true) {
                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.checked = true;
                        checkbox.disabled = true;
                        span.appendChild(checkbox);
                    } else {
                        const formatter = formatters[fieldDef.type] || (val => val !== undefined ? String(val) : "");
                        span.textContent = formatter(record[fieldName], fieldDef);
                    }

                    td.appendChild(span);
                    tr.appendChild(td);
                });

                fragment.appendChild(tr);
            });

            if (currNode) {
                currNode.parentElement.classList.add('o_open');
                currNode.parentElement.after(fragment);
            } else {
                const tbody = this.rootRef.el.querySelector('tbody');
                if (tbody) {
                    tbody.appendChild(fragment);
                }
            }

            // Re-hook click events
            this._hookRowClick();

        } catch (error) {
            console.error("Error fetching child data:", error);
        }
    }

    fieldsList() {
        const fields = Object.keys(this.fields);
        if (!fields.includes(this.children_field)) {
            fields.push(this.children_field);
        }
        return fields;
    }

    activate(id) {
        const views = [[false, 'form']];

        // Get view id from the action
        if (this.action && this.action.views) {
            this.action.views.forEach(view => {
                if (view.type === 'form') {
                    views[0][0] = view.viewID;
                }
            });
        }

        const action = {
            name: this.arch.attrs.string || '',
            type: 'ir.actions.act_window',
            res_model: this.modelName,
            res_id: id,
            views: views,
            target: 'current',
        };

        this.actionService.doAction(action);
    }

    showcontent(currNode, recordId, show) {
        const row = currNode.parentElement;
        if (show) {
            row.classList.add('o_open');
        } else {
            row.classList.remove('o_open');
        }

        const record = this.records[recordId];
        if (!record || !record[this.children_field]) return;

        record[this.children_field].forEach(childId => {
            const childRow = this.rootRef.el.querySelector(`[id=treerow_${childId}][data-row-parent-id="${currNode.dataset.id}"]`);
            if (!childRow) return;

            if (childRow.classList.contains('o_open')) {
                if (show) {
                    childRow.classList.add('o_open');
                } else {
                    childRow.classList.remove('o_open');
                }
                this.showcontent(childRow, childId, false);
            }

            childRow.style.display = show ? '' : 'none';
        });
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