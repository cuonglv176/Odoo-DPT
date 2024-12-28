/** @odoo-module */

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
const { Component,reactive, onWillUnmount, onWillUpdateProps, useEffect, useRef, useState, onMounted, willStart } = owl;

export class ks_bullet_chart extends Component{
    setup(){
    var self =this;
    this.root =null;
    this.bulletRef = useRef("bullet");
    useEffect(() => {
        if (this.root){
            this.root.dispose()
        }
        this._Ks_render()
        });

}

      _Ks_render(){
        var self = this;
        var rec = this.props.record.data;
        var rec = this.props.record.data;
        if ($(self.bulletRef.el).find("div.graph_text").length){
            $(self.bulletRef.el).find("div.graph_text").remove();
        }
        if (rec.ks_dashboard_item_type === 'ks_bullet_chart'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.bulletRef.el).append($("<div class='graph_text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.bulletRef.el).append($("<div class='graph_text'>").text("Select Group By to create chart view"));
                    } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.bulletRef.el).append($("<div class='graph_text'>").text("Select Measure and Group By to create chart view"));
                    } else if (!rec.ks_chart_data_count_type) {
                        $(self.bulletRef.el).append($("<div class='graph_text'>").text("Select Chart Data Count Type"));
                    } else {
                        this.get_bullet_chart(rec);
                    }
                } else {
                    $(self.bulletRef.el).append($("<div class='graph_text'>").text("Select a Model first."));
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        this.get_bullet_chart(rec);
                } else {
                    $(self.bulletRef.el).append($("<div class='graph_text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else {
                    $(self.bulletRef.el).append($("<div class='graph_text'>").text("Please run the appropriate Query"));
            }

        }
    }
    get_bullet_chart(rec){

        if($(this.bulletRef.el).find(".graph_text").length){
            $(this.bulletRef.el).find(".graph_text").remove();
        }
        const chart_data = JSON.parse(this.props.record.data.ks_chart_data);
        var ks_labels = chart_data['labels'];
        var ks_data = chart_data.datasets;

        let data=[];
        if (ks_data.length){
            for (let i=0 ; i<ks_labels.length ; i++){
                let data2={};
                for (let j=0 ;j<ks_data.length ; j++){
                    data2[`value${j+1}`] = ks_data[j].data[i]
                }
                data2["category"] = ks_labels[i]
                data.push(data2)
            }

            this.root = am5.Root.new(this.bulletRef.el);

            const theme = this.props.record.data.ks_chart_item_color
            switch(theme){
            case "default":
                this.root.setThemes([am5themes_Animated.new(this.root)]);
                break;
            case "dark":
                this.root.setThemes([am5themes_Dataviz.new(this.root)]);
                break;
            case "material":
                this.root.setThemes([am5themes_Material.new(this.root)]);
                break;
            case "moonrise":
                this.root.setThemes([am5themes_Moonrise.new(this.root)]);
                break;
            };

            // Create chart

            var chart = this.root.container.children.push(am5xy.XYChart.new(this.root, {
                panX: true,
                panY: false,
                wheelX: "panX",
                wheelY: "zoomX",
                layout: this.root.verticalLayout
            }));


            // Create axes

            var xRenderer = am5xy.AxisRendererX.new(this.root, {
                minGridDistance: 70
            });

            var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(this.root, {
                categoryField: "category",
                renderer: xRenderer,
                tooltip: am5.Tooltip.new(this.root, {
                themeTags: ["axis"],
                animationDuration: 200
                })
            }));

            xRenderer.grid.template.setAll({
            location: 1
            })

            xAxis.data.setAll(data);
            xAxis.get("renderer").labels.template.setAll({
              oversizedBehavior: "wrap",
              maxWidth: 100,
              textAlign: "center"
            });


            var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(this.root, {
                min: 0,
                renderer: am5xy.AxisRendererY.new(this.root, {
                strokeOpacity: 0.1
                })
            }));

            // Add series

            for (let k = 0;k<ks_data.length ; k++){
                var series = chart.series.push(am5xy.ColumnSeries.new(this.root, {
                    name: `${ks_data[k].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueYField:`value${k+1}`,
                    categoryXField: "category",
                    clustered: false,
                    tooltip: am5.Tooltip.new(this.root, {
                    labelText: `${ks_data[k].label}: {valueY}`
                    })
                }));

                series.columns.template.setAll({
                    width: am5.percent(80-(10*k)),
                    tooltipY: 0,
                    strokeOpacity: 0
                });
                series.data.setAll(data);
            }

            var legend = chart.children.unshift(am5.Legend.new(this.root, {
                centerX: am5.p50,
                x: am5.p50,
                marginTop: 15,
                marginBottom: 15
            }));
            if(this.props.record.data.ks_hide_legend==true){
                legend.data.setAll(chart.series.values);
            }

            if (this.props.record.data.ks_show_data_value == true){
                var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {}));
            }
            var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {
                behavior: "none"
                })
            );
            cursor.lineY.set("visible", false);
            cursor.lineX.set("visible", false);


            chart.appear(1000, 100);
            series.appear();
        }else{
            $(this.bulletRef.el).append($("<div class='graph_text'>").text("No Data Available."));
        }

    }
}
ks_bullet_chart.template = "Ksbulletchart";
export const ks_bullet_chart_field = {
    component:ks_bullet_chart,
    supportedTypes : ["char"]
};
registry.category("fields").add("ks_bullet_chart", ks_bullet_chart_field);