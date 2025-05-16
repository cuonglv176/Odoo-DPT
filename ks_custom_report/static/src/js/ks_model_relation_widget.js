/** @odoo-module **/
import { registry } from "@web/core/registry";
import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component, useState, onWillStart, useEffect } = owl;

export class KsQueryBuilder extends Component {
    setup() {
        this.state = useState({
            fieldName: this.props.value || 'id',
            resModel: this.props.record.data.ks_model_name || false
        });

        useEffect(() => {
            if (this.props.record.data.ks_model_name) {
                this.state.resModel = this.props.record.data.ks_model_name;
            }
        });
    }

    async onFieldChange(fieldName) {
        this.state.fieldName = fieldName;
        this.props.update(fieldName);
    }
}

KsQueryBuilder.template = "ks_model_relations.KsQueryBuilder";
KsQueryBuilder.components = { ModelFieldSelector };
KsQueryBuilder.props = {
    ...standardFieldProps,
    options: { type: Object, optional: true }
};

registry.category("fields").add('ks_model_relations', KsQueryBuilder);
