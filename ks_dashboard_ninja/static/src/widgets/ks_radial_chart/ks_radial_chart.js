/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, useEffect, useRef, useState } = owl;



export class Ks_radialBar_chart extends Component {

    setup() {
         var self =this;
         this.root =null;
         this.radialContainerRef = useRef("radialContainer");
         useEffect(() =>{
            if (this.root){
                this.root.dispose()
            }
            this._Ks_render()
            });

    }

     _Ks_render(){
        var self = this;
        var rec = this.props.record.data;
        if ($(self.radialContainerRef.el).find("div.graph_text").length){
           $(self.radialContainerRef.el).find("div.graph_text").remove();
        }
        if (rec.ks_dashboard_item_type == 'ks_radialBar_chart'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Select Group By to create chart view"));
                    } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Select Measure and Group By to create chart view"));
                    } else if (!rec.ks_chart_data_count_type) {
                        $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Select Chart Data Count Type"));
                    } else {
                        this._GetRadialData(rec);
                    }
                } else {
                    $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Select a Model first."));
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        this._GetRadialData(rec);
                } else {
                    $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else {
                    $(self.radialContainerRef.el).append($("<div class='graph_text'>").text("Please run the appropriate Query"));
            }
        }
     }

     _GetRadialData(rec){
        if($(this.radialContainerRef.el).find(".graph_text").length){
           $(this.radialContainerRef.el).find(".graph_text").remove();
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
            this.root = am5.Root.new(this.radialContainerRef.el);

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
            var chart = this.root.container.children.push(am5radar.RadarChart.new(this.root, {
              panX: false,
              panY: false,
              wheelX: "panX",
              wheelY: "zoomX",
            }));

            // Create axes and their renderers
            var xRenderer = am5radar.AxisRendererCircular.new(this.root, {
              strokeOpacity: 0.1,
              minGridDistance: 50
            });

            xRenderer.labels.template.setAll({
              radius: 25,
              maxPosition: 0.98
            });

            var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(this.root, {
              renderer: xRenderer,
              extraMax: 0.1,
              tooltip: am5.Tooltip.new(this.root, {})
            }));

            var yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(this.root, {
              categoryField: "category",
              renderer: am5radar.AxisRendererRadial.new(this.root, { minGridDistance: 20 })
            }));
            yAxis.get("renderer").labels.template.setAll({
               oversizedBehavior: "truncate",
               textAlign: "center",
               maxWidth: 100,
               ellipsis: "..."
            });

            // Create series
            for (var i = 0; i <chart_data.datasets.length; i++) {
              var series = chart.series.push(am5radar.RadarColumnSeries.new(this.root, {
                stacked: true,
                name:`${chart_data.datasets[i].label}`,
                xAxis: xAxis,
                yAxis: yAxis,
                valueXField: `value${i+1}`,
                categoryYField: "category"
              }));

              series.set("stroke",this.root.interfaceColors.get("background"));
              series.columns.template.setAll({
                width: am5.p100,
                strokeOpacity: 0.1,
                tooltipText: "{name}: {valueX}  {category}"
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

            if(this.props.record.data.ks_radial_legend==true){
                legend.data.setAll(chart.series.values);
            }

            if (this.props.record.data.ks_show_data_value == true){
                var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {}));
            }

            yAxis.data.setAll(data);

            // Animate chart and series in
            chart.appear(1000, 100);
        }else{
              $(this.radialContainerRef.el).append($("<div class='graph_text'>").text("No Data Available."));
        }
    }

}

Ks_radialBar_chart.template = "KsRadialBarChart";
export const ks_radial_chart_field = {
    component : Ks_radialBar_chart,
    supportedTypes : ["char"]
}

registry.category("fields").add("ks_dashboard_radial_chart", ks_radial_chart_field);