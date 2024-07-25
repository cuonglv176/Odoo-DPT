/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { registry } from "@web/core/registry";
import { Pager } from "@web/core/pager/pager";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from '@web/core/utils/hooks';

export class O2MListRenderer extends ListRenderer {
   get hasSelectors() {
       this.props.allowSelectors = true
       let list = this.props.list
       list.selection = list.records.filter((rec) => rec.selected)
       list.selectDomain = (value) => {
           list.isDomainSelected = value;
           list.model.notify();
       }
       return this.props.allowSelectors && !this.env.isSmall;
   }
   toggleSelection() {
       const list = this.props.list;
       if (!this.canSelectRecord) {
           return;
       }
       if (list.selection.length === list.records.length) {
           list.records.forEach((record) => {
               record.toggleSelection(false);
               list.selectDomain(false);
           });
       } else {
           list.records.forEach((record) => {
               record.toggleSelection(true);
           });
       }
   }
   get selectAll() {
       const list = this.props.list;
       const nbDisplayedRecords = list.records.length;
       if (list.isDomainSelected) {
         return true;
       }
       else {
         return false
       }
   }
}

export class O2mMultiSelect extends X2ManyField {
   setup() {
       super.setup();
       X2ManyField.components = { Pager, KanbanRenderer, ListRenderer: O2MListRenderer };
       this.orm = useService('orm');
       this.dialog = useService("dialog");
   }
   get Selected(){
       return this.list.records.filter((rec) => rec.selected).length
   }
   async ActionSelected(){
       let selectedRecords = this.list.records.filter((rec) => rec.selected)
       let selectedRecordIds = selectedRecords.map(function (item) {
            return item.data.id;
        });
       const message = await this.orm.call("dpt.sale.service.management", "action_create_account_payment_with_multiple_service", [selectedRecordIds]);
       if (message) {
            this.action.doAction(message)
       }
   }
}

export const O2manyMultiSelect = {
   ...x2ManyField,
   component: O2mMultiSelect,
};
O2mMultiSelect.template = "O2mMultiSelect";
registry.category("fields").add("one2many_select", O2manyMultiSelect);