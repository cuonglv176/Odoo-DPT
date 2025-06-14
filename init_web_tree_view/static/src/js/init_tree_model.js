/** @odoo-module */
// @ts-check

import { RelationalModel } from "@web/model/relational_model/relational_model";
import { orderByToString } from "@web/search/utils/order_by";
import { DynamicRecordList } from "@web/model/relational_model/dynamic_record_list";
import {
    FetchRecordError,
    extractInfoFromGroupData,
    getBasicEvalContext,
    getFieldsSpec,
    isRelational,
    makeActiveField,
} from "@web/model/relational_model/utils";

/**
 * @typedef Config
 * @property {string} resModel
 * @property {Object} fields
 * @property {Object} activeFields
 * @property {object} context
 * @property {boolean} isMonoRecord
 * @property {number} currentCompanyId
 * @property {boolean} isRoot
 * @property {Array} [domain]
 * @property {Array} [groupBy]
 * @property {Array} [orderBy]
 * @property {number} [resId]
 * @property {number[]} [resIds]
 * @property {string} [mode]
 * @property {number} [limit]
 * @property {number} [offset]
 * @property {number} [countLimit]
 * @property {number} [groupsLimit]
 * @property {Object} [groups]
 * @property {boolean} [openGroupsByDefault]
 * @property {string} [childFieldName]
 */

export class InitDynamicRecordTree extends DynamicRecordList {
  setup(config, data) {
    super.setup(config, data);
  }

  _setData(data) {
    super._setData(data);
    // update default level for each record
    this.records.forEach(r => {
      r.level = 0;
    })
  }

  removeRecordsByResIds(resIds) {
    this.records = this.records.filter(r => !resIds.includes(r.resId));
  }

}

export class InitTreeModel extends RelationalModel {
  static DynamicRecordList = InitDynamicRecordTree;

  async _loadUngroupedList(config) {
    config.limit = 0;

    // Update child field into field to fetch data from server
    let fieldSpec = getFieldsSpec(config.activeFields, config.fields, config.context)
    let domain = config.domain;
    const childField = config.fields[config.childFieldName]
    if (childField) {
      fieldSpec[config.childFieldName] = {}

      // get relation_field from childField
      const relationField = childField.relation_field;
      domain = [[relationField, '=', false], ...domain]
      // config.domain = [[relationField, '=', false], ...origin_domain];
    }

    const kwargs = {
      specification: fieldSpec,
      offset: config.offset,
      order: orderByToString(config.orderBy),
      limit: config.limit,
      context: { bin_size: true, ...config.context },
      count_limit: config.countLimit !== Number.MAX_SAFE_INTEGER ? config.countLimit + 1 : undefined,
    };

    return this.orm.webSearchRead(config.resModel, domain, kwargs);
  }

  async loadChildren(parentRecord, rowIndex, config) {
    let fieldSpec = getFieldsSpec(config.activeFields, config.fields, config.context)
    const childField = config.fields[config.childFieldName]
    if (childField) {
      fieldSpec[config.childFieldName] = {}
    }

    let domain = [['parent_id', '=', parentRecord.resId]];

    const kwargs = {
      specification: fieldSpec,
      offset: config.offset,
      order: orderByToString(config.orderBy),
      limit: config.limit,
      context: { bin_size: true, ...config.context },
      count_limit: config.countLimit !== Number.MAX_SAFE_INTEGER ? config.countLimit + 1 : undefined,
    };

    let data = await this.orm.webSearchRead(config.resModel, domain, kwargs);
    if (data.records.length > 0) {
      data.records.forEach(r => {
        let record = this.root._createRecordDatapoint(r);
        record.parentId = parentRecord.resId;
        record.level = parentRecord.level + 1;
        this.root._addRecord(record, rowIndex)
      })
    }
  }

  _getAllChildren(resId) {
    /** @type {Record[]} */
    let children = this.root.records.filter(r => r.parentId === resId);

    if (children.length > 0) {
      children.forEach(r => {
        children.push(...this._getAllChildren(r.resId))
      })
    }
    return children
  }

  removeChildren(record) {
    // get all children of resId
    let allChildren = this._getAllChildren(record.resId);
    let allChildrenIds = allChildren.map(r => r.resId);
    // remove all records in allChildren from records
    this.root.removeRecordsByResIds(allChildrenIds);
  }
}