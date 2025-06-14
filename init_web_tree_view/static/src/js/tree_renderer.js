/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Field, getPropertyFieldInfo } from "@web/views/fields/field";
import { ViewButton } from "@web/views/view_button/view_button";
import { Widget } from "@web/views/widgets/widget";

import { ListRenderer } from "@web/views/list/list_renderer";

export class InitTreeRenderer extends ListRenderer {
  setup() {
    let res = super.setup();
    // store childFieldName from props.list._config to this.childFieldName
    this.childFieldName = this.props.list._config.childFieldName;
    return res
  }

  onClickSortColumn(column) {
    console.log('Do not sort anymore')
  }

  /**
   *
   * @param {KeyboardEvent} ev
   * @param { import('@web/model/relational_model/group').Group | null } group
   * @param { import('@web/model/relational_model/record').Record | null } record
   */
  onCellKeydown(ev, group = null, record = null) {
    console.log('Do nothing on Cell Keydown');
  }

  toggleSelection() {
    console.log('Stop doing selection');
  }

  toggleRecordSelection() {
    console.log('Stop doing selection');
  }

  getColumns(record) {
    let res = super.getColumns(record);
    // convert res to array of res and index
    return res.map((col, index) => {
      col.index = index;
      return col;
    })
  }

  /**
   * @param { import('@web/model/relational_model/record').Record | null } record
   * @param {Object} column
   * @param {PointerEvent} ev
   */
  async onCellClicked(record, column, ev) {
    if (column.index === 0) {
      this.toggleOpenRow(ev, record);
    } else {
      return super.onCellClicked(record, column, ev);
    }
  }

  /**
   *
   * @param {PointerEvent} ev
   * @param { import('@web/model/relational_model/record').Record | null } record
   */
  toggleOpenRow(ev, record) {
    // get row index from ev KeyboardEvent
    const rowIndex = ev.target.closest('tr').rowIndex;

    // get resId from record
    const resId = record.resId || null;

    const row = $(ev.target.closest('tr'));
    if (row.hasClass('o_open')) {
      row.removeClass('o_open');
      this.props.list.model.removeChildren(record);
    } else {
      row.addClass('o_open');
      this.props.list.model.loadChildren(record, rowIndex, this.props.list._config);
    }
  }


  childFieldCount(record) {
    // get childFieldCount from record
    return record.data[this.childFieldName].count;

  }
}

InitTreeRenderer.template = 'init_web_tree_view.InitTreeRenderer';
InitTreeRenderer.rowsTemplate = 'init_web_tree_view.InitTreeRenderer.Rows';
InitTreeRenderer.recordRowTemplate = 'init_web_tree_view.InitTreeRenderer.RecordRow';

InitTreeRenderer.components = {
  DropdownItem,
  Field,
  ViewButton,
  CheckBox,
  Dropdown,
  Widget
};

// odoo.define('init_web_tree_view.TreeRenderer', function (require) {
// "use strict";
//
// var AbstractRenderer = require('web.AbstractRenderer');
// var core = require('web.core');
// var QWeb = core.qweb;
// var data = require('web.data');
// var field_utils = require('web.field_utils');
//
// var TreeRenderer = AbstractRenderer.extend({
//     /**
//      * @override
//      * @returns {Deferred}
//      */
//      init: function (parent, state, params) {
//         this._super.apply(this, arguments);
//         this.modelName = params.model;
//         this.fields = params.fields;
//         this.arch = params.arch;
//         this.children_field = params.children_field || 'child_ids';
//         this.dataset = new data.DataSet(this, this.modelName, params.context || {});
//         this.records = {};
//         _.bindAll(this, 'color_for');
//     },
//     fields_list: function () {
//         var fields = _.keys(this.fields);
//         if (!_(fields).contains(this.children_field)) {
//             fields.push(this.children_field);
//         }
//         return fields;
//     },
//     willStart: function () {
//         if (this.arch.attrs.colors) {
//             this.colors = _(this.arch.attrs.colors.split(';')).chain()
//                 .compact()
//                 .map(function(color_pair) {
//                     var pair = color_pair.split(':'),
//                         color = pair[0],
//                         expr = pair[1];
//                     return [color, py.parse(py.tokenize(expr)), expr];
//                 }).value();
//         }
//
//         return this._super();
//     },
//     start: function () {
//         var self = this;
//         var has_toolbar = !!this.arch.attrs.toolbar;
//         this.hook_row_click();
//         var html = QWeb.render('init_web_tree_view.TreeView', {
//             'title': this.arch.attrs.string,
//             'fields_view': this.arch.children,
//             'fields': this.fields,
//             'toolbar': has_toolbar
//         });
//         this.$el.html(html);
//         this.$el.addClass(this.arch.attrs['class']);
//         var records = this.getParent().model.data.data;
//         self.getdata(null, _(records).pluck('id'));
//         return this._super();
//     },
//         /**
//      * Returns the color for the provided record in the current view (from the
//      * ``@colors`` attribute)
//      *
//      * @param {Object} record record for the current row
//      * @returns {String} CSS color declaration
//      */
//     color_for: function (record) {
//         if (!this.colors) { return ''; }
//         for(var i=0, len=this.colors.length; i<len; ++i) {
//             var pair = this.colors[i],
//                 color = pair[0],
//                 expression = pair[1];
//             if (py.PY_isTrue(py.evaluate(expression, record))) {
//                 return 'color: ' + color + ';';
//             }
//         }
//         return '';
//     },
//     /**
//      * Sets up opening a row
//      */
//     hook_row_click: function () {
//         var self = this;
//         this.$el.delegate('.treeview-td span, .treeview-tr span', 'click', function (e) {
//             e.stopImmediatePropagation();
//             self.activate($(this).closest('tr').data('id'));
//         });
//
//         this.$el.delegate('.treeview-tr',  'click', function () {
//             var is_loaded = 0,
//                 $this = $(this),
//                 record_id = $this.data('id'),
//                 row_parent_id = $this.data('row-parent-id'),
//                 record = self.records[record_id],
//                 children_ids = record[self.children_field];
//
//             _(children_ids).each(function(childid) {
//                 if (self.$('[id=treerow_' + childid + '][data-row-parent-id='+ record_id +']').length ) {
//                     if (self.$('[id=treerow_' + childid + '][data-row-parent-id='+ record_id +']').is(':hidden')) {
//                         is_loaded = -1;
//                     } else {
//                         is_loaded++;
//                     }
//                 }
//             });
//             if (is_loaded === 0) {
//                 if (!$this.parent().hasClass('o_open')) {
//                     self.getdata(record_id, children_ids);
//                 }
//             } else {
//                 self.showcontent($this, record_id, is_loaded < 0);
//             }
//         });
//     },
//     // get child data of selected value
//     getdata: function (id, children_ids) {
//         var self = this;
//         self.dataset.read_ids(children_ids, this.fields_list()).then(function(records) {
//             _(records).each(function (record) {
//                 self.records[record.id] = record;
//             });
//             var $curr_node = self.$('#treerow_' + id);
//             var children_rows = QWeb.render('TreeView.rows', {
//                 'records': records,
//                 'children_field': self.children_field,
//                 'fields_view': self.arch.children,
//                 'fields': self.fields,
//                 'level': $curr_node.data('level') || 0,
//                 'format': field_utils.format,
//                 'color_for': self.color_for,
//                 'row_parent_id': id
//             });
//             if ($curr_node.length) {
//                 $curr_node.addClass('o_open');
//                 $curr_node.after(children_rows);
//             }
//             else {
//                 self.$('tbody').html(children_rows);
//             }
//         });
//     },
//
//     // Get details in listview
//     activate: function(id) {
//         var self = this;
//         var action = {
//             name: self.arch.attrs.string,
//             type: 'ir.actions.act_window',
//             res_model: self.modelName,
//             views: [[false, 'list'], [false, 'form']],
//             target: 'current',
//             domain: [['id', 'in', [id]]],
//             context: {},
//         };
//         self.do_action(action);
//     },
//
//     // show & hide the contents
//     showcontent: function (curnode,record_id, show) {
//         curnode.parent('tr').toggleClass('o_open', show);
//         _(this.records[record_id][this.children_field]).each(function (child_id) {
//             var $child_row = this.$('[id=treerow_' + child_id + '][data-row-parent-id='+ curnode.data('id') +']');
//             if ($child_row.hasClass('o_open')) {
//                 $child_row.toggleClass('o_open',show);
//                 this.showcontent($child_row, child_id, false);
//             }
//             $child_row.toggle(show);
//         }, this);
//     },
//
// });
//
// return TreeRenderer;
//
// });