/** @odoo-module **/
//odoo.define("ks_custom_report.GraphRenderer", function(require){
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { patch } from "@web/core/utils/patch";

//    var GraphRenderer = require("web.GraphRenderer");
const { } = owl;
    patch(GraphRenderer.prototype, "KsGraphRender",{


        async ksDoAction(domain){
            await this.props.model.getKsmodelDomain(domain);
        },

        async onGraphClicked(ev) {
            const [activeElement] = this.chart.getElementAtEvent(ev);
            if (!activeElement) {
                return;
            }
            const { _datasetIndex, _index } = activeElement;
            const { domains } = this.chart.data.datasets[_datasetIndex];
            if (domains) {
                await this.ksDoAction(domains[_index]);
            }
        },


});