/** @odoo-module **/

import { reactive } from "@odoo/owl";

export class TreeModel {
    constructor(env, params) {
        this.env = env;
        this.orm = env.services.orm;
        this.resModel = params.resModel;
        this.fieldNames = params.fieldNames || [];
        this.resId = params.resId;
        this.data = reactive({
            domain: params.domain || [],
            context: params.context || {},
            data: [],
        });
    }

    async load() {
        return this._fetchDataForTree();
    }

    async _fetchDataForTree() {
        const domain = [['parent_id', '=', false], ...this.data.domain];

        try {
            const records = await this.orm.searchRead(
                this.resModel,
                domain,
                [],
                { context: this.data.context }
            );
            this.data.data = records;
            return this.data;
        } catch (error) {
            console.error("Error fetching tree data:", error);
            return { data: [] };
        }
    }

    async reload() {
        return this._fetchDataForTree();
    }
}