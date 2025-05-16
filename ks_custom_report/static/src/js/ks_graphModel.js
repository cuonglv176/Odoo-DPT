/** @odoo-module */

import { GraphModel } from "@web/views/graph/graph_model";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { sortBy } from "@web/core/utils/arrays";
import { SEP } from "@web/views/graph/graph_model";

const { useEffect, onMounted } = owl;

patch(GraphModel.prototype, {
    /**
     * @override
     */
    setup(params) {
        this._super.apply(this, arguments);
        this.rpc = useService("rpc");
        this.action = useService("action");
    },

    async getKsmodelDomain(domain) {
        const context = browser.localStorage.getItem('user_context') ?
            JSON.parse(browser.localStorage.getItem('user_context')) : {};
        const result = await this.rpc(
                '/ks_custom_report/get_model_name',
                {
                    model: this.metaData.resModel,
                    local_context: context,
                    domain: domain,
                }
        );

        if (result) {
                 this.env.services.action.doAction(result);
            }
        },
});