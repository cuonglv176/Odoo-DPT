/** @odoo-module **/
import { registry } from "@web/core/registry";
import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
import { ModelFieldSelectorPopover } from "@web/core/model_field_selector/model_field_selector_popover";


const { Component } = owl;

export class KsQueryBuilder extends Component{
    setup() {
    var self= this;
    }
     async onFieldChange(fieldName){
    const changes = fieldName ;
    this.props.update(changes)
        }
};
Object.assign(KsQueryBuilder, {
    template: "ks_model_relations.KsQueryBuilder",
    components: {
        ModelFieldSelector,
    },
});


registry.category("fields").add('ks_model_relations', KsQueryBuilder);

