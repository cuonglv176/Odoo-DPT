/** @odoo-module **/

/*global L*/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
const { Component, useEffect, useRef, useState } = owl;

export class Ks_flower_chart extends Component {
    setup() {
        var self =this;
        this.root =null;
        this.flowerContainerRef = useRef("flowerContainer");
        useEffect(() =>{
            if(this.root){
                this.root.dispose()
            }
            this._Ks_render()
        });
    }

    _Ks_render() {
        var self = this;
        var rec = this.props.record.data;
        if ($(self.flowerContainerRef.el).find(".graph_text").length){
            $(self.flowerContainerRef.el).find(".graph_text").remove();
        }
        if (rec.ks_dashboard_item_type === 'ks_flower_view'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Select Group By to create chart view"));
                    } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Select Measure and Group By to create chart view"));
                    } else if (!rec.ks_chart_data_count_type) {
                        $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Select Chart Data Count Type"));
                    } else {
                        this.get_flower_data(rec);
                    }
                } else {
                    $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Select a Model first."));
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        this.get_flower_data(rec);
                } else {
                    $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else {
                    $(self.flowerContainerRef.el).append($("<div class='graph_text'>").text("Please run the appropriate Query"));
            }
        }
    }

    get_flower_data(rec) {
        if($(this.flowerContainerRef.el).find(".graph_text").length){
            $(this.flowerContainerRef.el).find(".graph_text").remove();
        }
        const chart_data = JSON.parse(this.props.record.data.ks_chart_data);
        var ks_labels = chart_data['labels'];
        var ks_data=[];
        let data = [];
        if (chart_data.datasets){
            for (let i=0 ; i<chart_data.datasets.length ; i++){
                ks_data.push({"ks_data":chart_data.datasets[i].data});
            }
        }
        if (ks_data.length){
            for (let i=0 ; i<chart_data.datasets.length ; i++){
                ks_data.push({"ks_data":chart_data.datasets[i].data});
                for (let j=0 ; j<ks_labels.length ; j++){
                    if (data.length != 0){
                        if (data[j]){
                            data[j][`value${i+1}`] = ks_data[i].ks_data[j]
                        }else{
                            let new_data = {};
                            new_data['category'] = ks_labels[j];
                            new_data[`value${i+1}`] = ks_data[i].ks_data[j];
                            data.push(new_data)
                        }
                    }else{
                        let new_data = {};
                        new_data['category'] = ks_labels[j];
                        new_data[`value${i+1}`] = ks_data[i].ks_data[j];
                        data.push(new_data)
                    }
                }
            }
            // Create root and chart
            this.root = am5.Root.new(this.flowerContainerRef.el);
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

            var chart = this.root.container.children.push(
              am5radar.RadarChart.new(this.root, {
                wheelY: "zoomX",
                wheelX: "panX",
                panX: false,
                panY: false,
              })
            );

            // Add cursor
            var cursor = chart.set("cursor", am5radar.RadarCursor.new(this.root, {
              behavior: "zoomX"
            }));

            cursor.lineY.set("visible", false);

            // Create axes and their renderers
            var xRenderer = am5radar.AxisRendererCircular.new(this.root, {
              cellStartLocation: 0.2,
              cellEndLocation: 0.8
            });

            xRenderer.labels.template.setAll({
              radius: 25
            });

            var xAxis = chart.xAxes.push(
              am5xy.CategoryAxis.new(this.root, {
                maxDeviation: 0,
                categoryField: "category",
                renderer: xRenderer,
                tooltip: am5.Tooltip.new(this.root, {})
              })
            );

            xAxis.data.setAll(data);
            xAxis.get("renderer").labels.template.setAll({
               oversizedBehavior: "truncate",
               textAlign: "center",
               maxWidth: 200,
               ellipsis: "..."
            });

            var yAxis = chart.yAxes.push(
              am5xy.ValueAxis.new(this.root, {
                renderer: am5radar.AxisRendererRadial.new(this.root, {})
              })
            );

            // Create series
            for (var i = 0; i <chart_data.datasets.length ; i++) {
              var series = chart.series.push(
                am5radar.RadarColumnSeries.new(this.root, {
                  name: `${chart_data.datasets[i].label}`,
                  xAxis: xAxis,
                  yAxis: yAxis,
                  valueYField: `value${i+1}`,
                  categoryXField: "category"
                })
              );

              series.columns.template.setAll({
                tooltipText: "{name}: {valueY}",
                width: am5.percent(100)
              });

              series.data.setAll(data);

              series.appear(1000);
            }

            var legend = chart.children.push(
                am5.Legend.new(this.root, {
                    centerX: am5.percent(100),
                    x: am5.percent(100),
                    layout: this.root.verticalLayout
                })
            );

            if(this.props.record.data.ks_hide_legend==true){
                legend.data.setAll(chart.series.values);
            }

            if (this.props.record.data.ks_show_data_value == true){
                var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {}));
            }

            // Animate chart
            chart.appear(1000, 100);
        }else{
            $(this.flowerContainerRef.el).append($("<div class='graph_text'>").text("No Data Available."));
        }
    }
}


Ks_flower_chart.template = "KsFlowerChart";
export const ks_flower_chart_field = {
    component : Ks_flower_chart,
    supportedTypes : ["char"]
}
registry.category("fields").add("ks_dashboard_flower_chart", ks_flower_chart_field);