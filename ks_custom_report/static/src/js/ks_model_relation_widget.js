/** @odoo-module **/
import { registry } from "@web/core/registry";
import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
const { Component, useState } = owl;

export class KsQueryBuilder extends Component {
    setup() {
        this.state = useState({
            fieldName: this.props.value || 'id'
        });
    }
    async onFieldChange(fieldName) {
        this.props.update(fieldName);
    }
}
KsQueryBuilder.template = "ks_model_relations.KsQueryBuilder";
KsQueryBuilder.components = { ModelFieldSelector };
registry.category("fields").add('ks_model_relations', KsQueryBuilder);
