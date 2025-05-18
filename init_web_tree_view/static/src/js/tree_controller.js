/** @odoo-module **/

import {_t} from '@web/core/l10n/translation';
import { Layout } from "@web/search/layout";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { ListController } from '@web/views/list/list_controller';

import { Component,  useRef, useState, useSubEnv, useEffect, onWillStart, onMounted, onWillPatch } from '@odoo/owl';
import { useService, useBus } from "@web/core/utils/hooks";
import { useModelWithSampleData } from "@web/model/model";
import { executeButtonCallback, useViewButtons } from "@web/views/view_button/view_button_hook";
import { useSetupView } from "@web/views/view_hook";
import { usePager } from "@web/search/pager_hook";


export class InitTreeController extends ListController {
  setup() {
    // super.setup();

    this.actionService = useService('action');
    this.dialogService = useService('dialog');
    this.userService = useService('user');
    this.rpc = useService('rpc');
    this.rootRef = useRef('root');

    this.archInfo = this.props.archInfo;

    // * INIT start add custom
    const { xmlDoc } = this.archInfo;
    const { attributes } = xmlDoc;
    const { child_field } = attributes;
    this.childFieldName = child_field.value
    // * INIT end add custom

    const openFormView = this.props.editable ? this.archInfo.openFormView : false;
    this.onOpenFormView = openFormView ? this.openRecord.bind(this) : undefined;
    this.activeActions = this.archInfo.activeActions;
    this.editable =
        this.activeActions.edit && this.props.editable ? this.archInfo.editable : false;
    this.model = useState(useModelWithSampleData(this.props.Model, this.modelParams));

    // In multi edition, we save or notify invalidity directly when a field is updated, which
    // occurs on the change event for input fields. But we don't want to do it when clicking on
    // "Discard". So we set a flag on mousedown (which triggers the update) to block the multi
    // save or invalid notification.
    // However, if the mouseup (and click) is done outside "Discard", we finally want to do it.
    // We use `nextActionAfterMouseup` for this purpose: it registers a callback to execute if
    // the mouseup following a mousedown on "Discard" isn't done on "Discard".
    this.hasMousedownDiscard = false;
    this.nextActionAfterMouseup = null;

    this.optionalActiveFields = [];

    onWillStart(async () => {
        this.isExportEnable = await this.userService.hasGroup("base.group_allow_export");
    });

    onMounted(() => {
        const { rendererScrollPositions } = this.props.state || {};
        if (rendererScrollPositions) {
            const renderer = this.rootRef.el.querySelector(".o_list_renderer");
            renderer.scrollLeft = rendererScrollPositions.left;
            renderer.scrollTop = rendererScrollPositions.top;
        }
    });

    this.archiveEnabled =
        "active" in this.props.fields
            ? !this.props.fields.active.readonly
            : "x_active" in this.props.fields
            ? !this.props.fields.x_active.readonly
            : false;
    useSubEnv({ model: this.model }); // do this in useModelWithSampleData?
    useViewButtons(this.model, this.rootRef, {
        beforeExecuteAction: this.beforeExecuteActionButton.bind(this),
        afterExecuteAction: this.afterExecuteActionButton.bind(this),
    });
    useSetupView({
        rootRef: this.rootRef,
        beforeLeave: async () => {
            return this.model.root.leaveEditMode();
        },
        beforeUnload: async (ev) => {
            const editedRecord = this.model.root.editedRecord;
            if (editedRecord) {
                const isValid = await editedRecord.urgentSave();
                if (!isValid) {
                    ev.preventDefault();
                    ev.returnValue = "Unsaved changes";
                }
            }
        },
        getLocalState: () => {
            const renderer = this.rootRef.el.querySelector(".o_list_renderer");
            return {
                modelState: this.model.exportState(),
                rendererScrollPositions: {
                    left: renderer.scrollLeft,
                    top: renderer.scrollTop,
                },
            };
        },
        getOrderBy: () => {
            return this.model.root.orderBy;
        },
    });

    // TODO try to remove
    // usePager(() => {
    //     const { count, hasLimitedCount, isGrouped, limit, offset } = this.model.root;
    //     return {
    //         offset: offset,
    //         limit: limit,
    //         total: count,
    //         onUpdate: async ({ offset, limit }, hasNavigated) => {
    //             if (this.model.root.editedRecord) {
    //                 if (!(await this.model.root.editedRecord.save())) {
    //                     return;
    //                 }
    //             }
    //             await this.model.root.load({ limit, offset });
    //             if (hasNavigated) {
    //                 this.onPageChangeScroll();
    //             }
    //         },
    //         updateTotal:
    //             !isGrouped && hasLimitedCount ? () => this.model.root.fetchCount() : undefined,
    //     };
    // });

    useEffect(
        () => {
            if (this.props.onSelectionChanged) {
                const resIds = this.model.root.selection.map((record) => record.resId);
                this.props.onSelectionChanged(resIds);
            }
        },
        () => [this.model.root.selection.length]
    );
    // this.searchBarToggler = useSearchBarToggler();
    this.firstLoad = true;
    onWillPatch(() => {
        this.firstLoad = false;
    });
    useBus(this.env.searchModel, "direct-export-data", this.onDirectExportData.bind(this));
  }

  get modelParams() {
    let modelParams = super.modelParams;
    let { config } = modelParams;
    // get activeFields, fields from config
    let { activeFields } = config;

    // add childFieldName into activeFields
    if (this.childFieldName) {
      activeFields = {
        ...activeFields,
        [this.childFieldName]: {
          'context': '{}',
          'required': false,
          // ? maybe need to add more properties
        },
      }
    }

    // update activeFields and childFieldName into config
    modelParams.config = {
      ...config,
      activeFields,
      'childFieldName': this.childFieldName,
    }
    return modelParams;
  }
}

InitTreeController.template = `init_web_tree_view.InitTree`;

InitTreeController.components = {
  Layout,
  CogMenu,
};

InitTreeController.defaultProps = {
  allowSelectors: false,
  createRecord: () => {
  },
  editable: false,
  selectRecord: () => {
  },
  showButtons: false,
};

// odoo.define('init_web_tree_view.TreeController', function (require) {
// "use strict";
//
// var AbstractController = require('web.AbstractController');
// var core = require('web.core');
// var _t = core._t;
// var QWeb = core.qweb;
//
// var TreeController = AbstractController.extend({
//     custom_events: {
//     },
//     init: function (parent, model, renderer, params) {
//         this._super.apply(this, arguments);
//         this.domain = params.domain || [];
//         this.context = params.context;
//     },
// });
//
// return TreeController;
//
// });