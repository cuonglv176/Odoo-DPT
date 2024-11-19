/** @odoo-module **/
import { Component, onWillStart, useState ,useEffect,onMounted, onWillUpdateProps,useRef,} from "@odoo/owl";
import {globalfunction } from '@ks_dashboard_ninja/js/ks_global_functions';
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { formatFloat } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";
import { localization } from "@web/core/l10n/localization";
import {formatDate,formatDateTime} from "@web/core/l10n/dates";
import {parseDateTime,parseDate,} from "@web/core/l10n/dates";
import { renderToElement } from "@web/core/utils/render";

export class Ksdashboardgraph extends Component{
    setup(){
        this.chart_container = {};
        this.actionService = useService("action");
        this._rpc = useService("rpc");
        this.state = useState({item_data:"",list_view_data:""})
        onMounted(() => this._update_view());
        this.item = this.props.item

        this.ks_dashboard_data = this.props.dashboard_data
        if (this.item.ks_dashboard_item_type == 'ks_list_view'){
            this.prepare_list()
        }else{
            this.prepare_item(this.item);
        }
        this.ks_gridstack_container = useRef("ks_gridstack_container");
        this.ks_list_view = useRef("ks_list_view")
        var update_interval = this.props.dashboard_data.ks_set_interval
         onWillUpdateProps(async(nextprops)=>{
            if(nextprops.ksdatefilter !='none'){
                await this.ksFetchUpdateItem(this.item.id)
            }
            if (Object.keys(nextprops.pre_defined_filter).length){
                if (nextprops.pre_defined_filter?.item_ids?.includes(this.item.id)){
                    await this.ksFetchUpdateItem(this.item.id)
                }
            }

        })
        useEffect(()=>{
            if (update_interval){
                const interval = setInterval(() => {
                    this.ksFetchUpdateItem(this.item.id);
                }, update_interval);
                return () => clearInterval(interval);
            }

        })
    }
    async ksFetchUpdateItem(item_id) {
            var self = this;
            await jsonrpc("/web/dataset/call_kw",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_item',
                args: [
                    [parseInt(item_id)], self.ks_dashboard_data.ks_dashboard_id,self.__owl__.parent.component.ksGetParamsForItemFetch(self.item.id)
                ],
                kwargs:{context:this.props.dashboard_data.context},
//                context: self.getContext(),
            }).then(function(new_item_data) {
                this.ks_dashboard_data.ks_item_data[item_id] = new_item_data[item_id];
                this.item = this.ks_dashboard_data.ks_item_data[item_id] ;
                // done this to render updated items on play button
                this.__owl__.parent.component.ks_dashboard_data.ks_item_data[this.item.id] = new_item_data[item_id]
                if (this.item.ks_dashboard_item_type =="ks_funnel_chart"){
                    $(this.ks_gridstack_container.el).find(".card-body").remove()
                    this.ksrenderfunnelchart($(this.ks_gridstack_container.el),this.item);
                }else if(this.item.ks_dashboard_item_type =="ks_list_view"){
                    this.prepare_list()
                }else if(this.item.ks_dashboard_item_type == ("ks_map_view")){
                    $(this.ks_gridstack_container.el).find(".card-body").remove()
                    this.ksrendermapview($(this.ks_gridstack_container.el),this.item)
                }else{
                    $(this.ks_gridstack_container.el).find(".card-body").remove()
                    this.ks_render_graphs($(this.ks_gridstack_container.el),this.item)
                }
//                 $(this.ks_gridstack_container.el).find(".ks_breadcrumb").addClass("d-none")
//                 $(this.ks_gridstack_container.el).find(".ks_chart_heading").removeClass("d-none")

            }.bind(this));
        }

    _update_view(){
        if(this.item.ks_dashboard_item_type == 'ks_list_view'){
            if (this.item.ks_pagination_limit < this.intial_count) {
            $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.intial_count < this.item.ks_pagination_limit ) {
             $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.item.ks_record_data_limit === this.item.ks_pagination_limit){
                $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.intial_count == 0){
             $(this.ks_list_view.el).find('.ks_pager').addClass('d-none');
        }
        if (this.item.ks_pagination_limit==0){
             $(this.ks_list_view.el).find('.ks_pager_name').addClass('d-none');
        }
        if (this.item.ks_data_calculation_type === 'query' || this.item.ks_list_view_type === "ungrouped"){
            $('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
        }
//        if (!this.item.ks_show_records) {
//            $('ks_info').hide();
//        }
        }else{
        $(this.ks_gridstack_container.el).addClass('ks_dashboarditem_id');
        $(this.ks_gridstack_container.el).find(".ks_dashboard_item_button_container").addClass("ks_funnel_item_container")
        if (this.item.ks_dashboard_item_type =="ks_funnel_chart"){
                this.ksrenderfunnelchart($(this.ks_gridstack_container.el),this.item);
        }else if(this.item.ks_dashboard_item_type == ("ks_map_view")){
            this.ksrendermapview($(this.ks_gridstack_container.el),this.item)
        }else{
            this.ks_render_graphs($(this.ks_gridstack_container.el),this.item)
        }
        }
    }

    prepare_list() {
        var self = this;
        if (this.item.ks_info){
            var ks_description = this.item.ks_info.split('\n');
            var ks_description = ks_description.filter(element => element !== '')
        }else {
            var ks_description = false;
        }
        if (typeof(this.item.ks_list_view_data) == 'string'){
            var list_view_data = JSON.parse(this.item.ks_list_view_data)
        }else{
             var list_view_data = this.item.ks_list_view_data
        }
        var data_rows = list_view_data.data_rows
        var length = data_rows ? data_rows.length: false;
        var item_id = this.item.id
        this.ks_info = ks_description;
        this.ks_chart_title = this.item.name
        this.ks_breadcrumb = this.item.ks_action_name
        this.item_id = item_id
        this.ksIsDashboardManager= self.ks_dashboard_data.ks_dashboard_manager,
        this.ksIsUser = true,
        this.ks_dashboard_list = self.ks_dashboard_data.ks_dashboard_list,
        this.count = '1-' + length
        this.offset = 1
        this.intial_count = length
        this.ks_pager = true
        this.ks_company= this.item.ks_company
        this.calculation_type = this.ks_dashboard_data.ks_item_data[this.item_id].ks_data_calculation_type

        if (this.item.ks_list_view_type === "ungrouped" && list_view_data) {
            if (list_view_data.date_index) {
                var index_data = list_view_data.date_index;
                for (var i = 0; i < index_data.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows.length; j++) {
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]
                        if (date) {
                            if( list_view_data.fields_type[index] === 'date'){
                                list_view_data.data_rows[j]["data"][index] = formatDate(parseDateTime(date), { format: localization.dateFormat })
                            } else{
                                list_view_data.data_rows[j]["data"][index] = formatDateTime(parseDateTime(date), { format: localization.dateTimeFormat })
                            }
                        }else{
                            list_view_data.data_rows[j]["data"][index] = "";
                        }
                    }
                }
            }
        }
        if (list_view_data) {
            for (var i = 0; i < list_view_data.data_rows.length; i++) {
                for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
                    if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
                        if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
                            list_view_data.data_rows[i].data[j] = formatFloat(list_view_data.data_rows[i].data[j], Float64Array, {digits:[0, self.item.ks_precision_digits]})
                        }
                    } else {
                        list_view_data.data_rows[i].data[j] = "";
                    }
                }
            }
        }
        this.state.list_view_data = list_view_data
        this.list_type = this.item.ks_list_view_type
        this.tmpl_list_type = self.ks_dashboard_data.ks_item_data[this.item_id].ks_list_view_type
        this.isDrill = this.ks_dashboard_data.ks_item_data[this.item_id]['isDrill']
        this.ks_show_records = this.item.ks_show_records
//        this.item.$el = $ks_gridstack_container;

    }

    prepare_item(item) {
     var self = this;
     var isDrill = item.isDrill ? item.isDrill : false;
     this.chart
     var chart_id = item.id;
     this.ksColorOptions = ["default","dark","moonrise","material"]
     var funnel_title = item.name;
     if (item.ks_info){
        var ks_description = item.ks_info.split('\n');
        var ks_description = ks_description.filter(element => element !== '')
     }else {
        var ks_description = false;
     }

     this.ks_chart_title= funnel_title,
     this.ksIsDashboardManager= self.ks_dashboard_data.ks_dashboard_manager,
     this.ksIsUser = true,
     this.ks_dashboard_list = self.ks_dashboard_data.ks_dashboard_list,
     this.chart_id = chart_id,
     this.ks_info = ks_description,
     this.ksChartColorOptions = this.ksColorOptions,
     this.ks_company = item.ks_company,
     this.ks_dashboard_item_type = item.ks_dashboard_item_type,
     this.ks_breadcrumb = item.ks_action_name
    }

    ks_render_graphs($ks_gridstack_container,item){
        var self =this;
            if($ks_gridstack_container.find('.ks_chart_card_body').length){
                var graph_render = $ks_gridstack_container.find('.ks_chart_card_body');
            }else{
                $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                 var graph_render = $ks_gridstack_container.find('.ks_chart_card_body');
            }
        const chart_data = JSON.parse(item.ks_chart_data);
        var ks_labels = chart_data['labels'];
        var ks_data = chart_data.datasets;

        let data=[];
        if (ks_data && ks_labels){
        if (ks_data.length && ks_labels.length){
            for (let i=0 ; i<ks_labels.length ; i++){
                let data2={};
                for (let j=0 ;j<ks_data.length ; j++){
                    if (ks_data[j].type == "line"){
                    data2[ks_data[j].label+'line'] = ks_data[j].data[i]
                    }else{
                    data2[ks_data[j].label] = ks_data[j].data[i]
                    }
                }
                data2["category"] = ks_labels[i]
                data.push(data2)
            }


            const root  = am5.Root.new(graph_render[0]);
            var self =this;

            const theme = item.ks_chart_item_color
            switch(theme){
            case "default":
                root.setThemes([am5themes_Animated.new(root)]);
                break;
            case "dark":
                root.setThemes([am5themes_Dataviz.new(root)]);
                break;
            case "material":
                root.setThemes([am5themes_Material.new(root)]);
                break;
            case "moonrise":
                root.setThemes([am5themes_Moonrise.new(root)]);
                break;
            };
            var chart_type = item.ks_dashboard_item_type
            switch (chart_type){
            case "ks_bar_chart":
            case "ks_bullet_chart":
            var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
             wheelX: "panX",wheelY: "zoomX",layout: root.verticalLayout}));

            var xRenderer = am5xy.AxisRendererX.new(root, {
                cellStartLocation: 0.1,
                cellEndLocation: 0.9
            });

            var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {categoryField: "category",
            renderer: xRenderer,tooltip: am5.Tooltip.new(root, {})}));

            xRenderer.grid.template.setAll({location: 1})

            xAxis.data.setAll(data);

            var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {min: 0,
            extraMax: 0.1,renderer: am5xy.AxisRendererY.new(root, {strokeOpacity: 0.1}) }));

            // Add series

            for (let k = 0;k<ks_data.length ; k++){
                if (item.ks_dashboard_item_type == "ks_bar_chart" && item.ks_bar_chart_stacked == true && ks_data[k].type != "line"){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        stacked: true,
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueYField:`${ks_data[k].label}`,
                        categoryXField: "category",
                        tooltip: am5.Tooltip.new(root, {
                        pointerOrientation: "horizontal",
                        labelText: "{categoryX}, {name}: {valueY}"
                        })
                    }));
                    series.columns.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series.data.setAll(data);
                }else if (item.ks_dashboard_item_type == "ks_bar_chart" && ks_data[k].type != "line"){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueYField:`${ks_data[k].label}`,
                        categoryXField: "category",
                        tooltip: am5.Tooltip.new(root, {
                        pointerOrientation: "horizontal",
                        labelText: "{categoryX}, {name}: {valueY}"
                        })

                    }));
                    series.columns.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series.data.setAll(data);

                }else if (item.ks_dashboard_item_type == "ks_bullet_chart"){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                    name: `${ks_data[k].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueYField:`${ks_data[k].label}`,
                    categoryXField: "category",
                    clustered: false,
                    tooltip: am5.Tooltip.new(root, {
                    labelText: `${ks_data[k].label}: {valueY}`
                    })
                    }));

                    series.columns.template.setAll({
                        width: am5.percent(80-(10*k)),
                        tooltipY: 0,
                        strokeOpacity: 0
                    });
                    series.columns.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series.data.setAll(data);
                }

                if (item.ks_show_records == true && series){
                    series.columns.template.setAll({
                        tooltipY: 0,
                        templateField: "columnSettings"
                   });
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                            behavior: "zoomY"
                    }));
                   cursor.lineY.set("forceHidden", true);
                   cursor.lineX.set("forceHidden", true);
                }

                if (item.ks_dashboard_item_type == "ks_bar_chart" && item.ks_chart_measure_field_2 && ks_data[k].type == "line"){
                    var series2 = chart.series.push(
                        am5xy.LineSeries.new(root, {
                            name: `${ks_data[k].label}`,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueYField:`${ks_data[k].label + "line"}`,
                            categoryXField: "category",
                            tooltip: am5.Tooltip.new(root, {
                                pointerOrientation: "horizontal",
                                labelText: "{categoryX}, {name}: {valueY}"
                            })
                        })
                    );

                    series2.strokes.template.setAll({strokeWidth: 3,templateField: "strokeSettings"});
                    series2.strokes.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series2.data.setAll(data);

                    series2.bullets.push(function() {
                        return am5.Bullet.new(root, {
                            sprite: am5.Circle.new(root, {
                                strokeWidth: 3,
                                stroke: series2.get("stroke"),
                                radius: 5,
                                fill: root.interfaceColors.get("background")
                            })
                        });
                    });
                }
            }
            break;
            case "ks_horizontalBar_chart":
                var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
                wheelX: "panX",wheelY: "zoomX",layout: root.verticalLayout}));
                var yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(root, {
                    categoryField: "category",
                    renderer: am5xy.AxisRendererY.new(root, {
                        inversed: true,
                        cellStartLocation: 0.1,
                        cellEndLocation: 0.9
                    })
                }))

                yAxis.data.setAll(data);

                var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
                    renderer: am5xy.AxisRendererX.new(root, {
                        strokeOpacity: 0.1
                    }),
                    min: 0
                }));
                for (let k = 0;k<ks_data.length ; k++){
                if (item.ks_bar_chart_stacked == true){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        stacked: true,
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueXField:`${ks_data[k].label}`,
                        categoryYField: "category",
                        sequencedInterpolation: true,
                        tooltip: am5.Tooltip.new(root, {
                        pointerOrientation: "horizontal",
                        labelText: "{categoryY}, {name}: {valueX}"
                        })
                    }));

                }else {
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueXField:`${ks_data[k].label}`,
                        categoryYField: "category",
                        sequencedInterpolation: true,
                        tooltip: am5.Tooltip.new(root, {
                        pointerOrientation: "horizontal",
                        labelText: "{categoryY}, {name}: {valueX}"
                        })

                }));
                }
                if (item.ks_show_records == true && series){
                    series.columns.template.setAll({
//                        width: am5.percent(80-(10*k)),
                        height: am5.p100,
                        strokeOpacity: 0
                   });
                   var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                            behavior: "zoomY"
                    }));
                   cursor.lineY.set("forceHidden", true);
                   cursor.lineX.set("forceHidden", true);
                }
                series.columns.template.events.on("click",function(ev){
                    if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                        self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                    }
                });
                 series.data.setAll(data);
            }
            break;
            case "ks_line_chart":
            case "ks_area_chart":
                var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
                wheelX: "panX",wheelY: "zoomX",layout: root.verticalLayout}));
                var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
                    categoryField: "category",
                    maxDeviation: 0.2,
                    renderer: am5xy.AxisRendererX.new(root, {}),
                    tooltip: am5.Tooltip.new(root, {})
                }));
                xAxis.data.setAll(data);

                var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {min: 0,
                extraMax: 0.1,renderer: am5xy.AxisRendererY.new(root, {strokeOpacity: 0.1}) }));

                for (let k = 0;k<ks_data.length ; k++){
                    var series = chart.series.push(am5xy.LineSeries.new(root, {
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueYField: `${ks_data[k].label}`,
                        categoryXField: "category",
                        alignLabels: true,
                        tooltip: am5.Tooltip.new(root, {
                            labelText: "[bold]{categoryX}[/]\n{name}: {valueY}"
                        })
                    }));
                    series.strokes.template.setAll({strokeWidth: 2,templateField: "strokeSettings"});

                    series.bullets.push(function() {
                        var graphics = am5.Rectangle.new(root, {
                            width:7,
                            height:7,
                            centerX:am5.p50,
                            centerY:am5.p50,
                            fill: series.get("stroke")
                        });
                        if (item.ks_dashboard_item_type == "ks_area_chart" || item.ks_dashboard_item_type == "ks_line_chart"){
                            graphics.events.on("click", function(ev) {
                                if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                        }
                        return am5.Bullet.new(root, {
                            sprite: graphics
                        });
                    });
                    if (item.ks_dashboard_item_type === "ks_area_chart"){
                        series.fills.template.setAll({
                            fillOpacity: 0.5,
                            visible: true
                        });
                    }

                    series.data.setAll(data);
                }

                if (item.ks_show_records == true){
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                        behavior: "none"
                    }));
                    cursor.lineY.set("forceHidden", true);
                    cursor.lineX.set("forceHidden", true);

                }
                break;
                case "ks_pie_chart":
                case "ks_doughnut_chart":
                    var series = []
                    if (item.ks_semi_circle_chart == true && (item.ks_dashboard_item_type == "ks_pie_chart" ||item.ks_dashboard_item_type == "ks_doughnut_chart")){
                         if (item.ks_dashboard_item_type == 'ks_doughnut_chart'){
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                   innerRadius : am5.percent(50),
                                   layout: root.verticalLayout,
                                   startAngle: 180,
                                   endAngle: 360,
                            }));
                        }else{
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                    radius: am5.percent(90),
                                    layout: root.verticalLayout,
                                    startAngle: 180,
                                    endAngle: 360,
                                }));
                        }
                        for (let k = 0;k<ks_data.length ; k++){
                            series[k] = chart.series.push(
                                am5percent.PieSeries.new(root, {
                                name: `${ks_data[k].label}`,
                                valueField: `${ks_data[k].label}`,
                                categoryField: "category",
                                alignLabels: true,
                                startAngle: 180,
                                endAngle: 360,
                            }));
                        }
                    }else{
                        if (item.ks_dashboard_item_type == "ks_doughnut_chart"){
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                innerRadius: am5.percent(50),
                                layout: root.verticalLayout,
                            }));
                        }else{
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                radius: am5.percent(90),
                                layout: root.verticalLayout,
                            }));
                        }
                        for (let k = 0;k<ks_data.length ; k++){
                            series[k] = chart.series.push(
                                am5percent.PieSeries.new(root, {
                                name: `${ks_data[k].label}`,
                                valueField: `${ks_data[k].label}`,
                                categoryField: "category",
                                alignLabels: true,
                            })
                            );
                        }
                    }
                    var bgColor = root.interfaceColors.get("background");
                    for (let rec of series){
                        rec.ticks.template.setAll({ forceHidden: true })
                        rec.labels.template.setAll({ forceHidden: true })
                        rec.slices.template.setAll({
                            stroke: bgColor,
                            strokeWidth: 2,
                            templateField: "settings",
                            });
                            rec.slices.template.events.on("click", function(ev) {
                                rec.slices.each(function(slice) {
                                    if(slice == ev.target && !self.ks_dashboard_data['ks_ai_dashboard']){
                                        self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                    }
                                })
                            });

                        if (item.ks_show_records == true){
                            rec.slices.template.setAll({
                                tooltipText:
                                    "[bold]{category}[/]\n{name}: {value}"
                            });
                        }
                        rec.data.setAll(data)
                        rec.appear(1000, 100);
                    }
                    break;
                case "ks_polarArea_chart":
                case "ks_radar_view":
                case "ks_flower_view":
                case "ks_radialBar_chart":
                    var chart = root.container.children.push(am5radar.RadarChart.new(root, {
                        panX: false,
                        panY: false,
                        wheelX: "panX",
                        wheelY: "zoomX",
                        radius: am5.percent(80),
//                        layout: root.verticalLayout,
                    }));

                    if (item.ks_dashboard_item_type == "ks_flower_view"){
                        var xRenderer = am5radar.AxisRendererCircular.new(root, {});
                        xRenderer.labels.template.setAll({
                            radius: 10,
                            cellStartLocation: 0.2,
                            cellEndLocation: 0.8
                        });
                    }else if (item.ks_dashboard_item_type == "ks_radialBar_chart"){
                        var xRenderer = am5radar.AxisRendererCircular.new(root, {
                            strokeOpacity: 0.1,
                            minGridDistance: 50
                         });
                        xRenderer.labels.template.setAll({
                            radius: 23,
                            maxPosition: 0.98
                        });
                    }else{
                        var xRenderer = am5radar.AxisRendererCircular.new(root, {});
                        xRenderer.labels.template.setAll({
                            radius: 10,
                        });
                    }
                    if (item.ks_dashboard_item_type == "ks_radialBar_chart"){
                        var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
                            renderer: xRenderer,
                            extraMax: 0.1,
                            tooltip: am5.Tooltip.new(root, {})
                        }));

                        var yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(root, {
                            categoryField: "category",
                            renderer: am5radar.AxisRendererRadial.new(root, { minGridDistance: 20 })
                        }));
                        yAxis.get("renderer").labels.template.setAll({
                            oversizedBehavior: "truncate",
                            textAlign: "center",
                            maxWidth: 150,
                            ellipsis: "..."
                        });
                    }else{
                        var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
                            maxDeviation: 0,
                            categoryField: "category",
                            renderer: xRenderer,
                            tooltip: am5.Tooltip.new(root, {})
                        }));
                        xAxis.data.setAll(data);

                        var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
                            renderer: am5radar.AxisRendererRadial.new(root, {})
                        }));
                    }
                    if (item.ks_dashboard_item_type == "ks_polarArea_chart"){
                        for (let k = 0;k<ks_data.length ; k++) {
                            var series = chart.series.push(am5radar.RadarColumnSeries.new(root, {
                            stacked: true,
                            name: `${ks_data[k].label}`,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueYField: `${ks_data[k].label}`,
                            categoryXField: "category",
                            alignLabels: true,
                            }));

                        series.set("stroke", root.interfaceColors.get("background"));
                        if (item.ks_show_records == true){
                            series.columns.template.setAll({
                                width: am5.p100,
                                strokeOpacity: 0.1,
                                tooltipText: "{name}: {valueY}"
                            });
                        }
                        series.columns.template.events.on("click",function(ev){
                            if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                            }
                        });
                        series.data.setAll(data);
                        }
                        xAxis.data.setAll(data);
                    }else if (item.ks_dashboard_item_type == "ks_flower_view"){
                        for (let k = 0;k<ks_data.length ; k++){
                            var series = chart.series.push(
                                am5radar.RadarColumnSeries.new(root, {
                                name: `${ks_data[k].label}`,
                                xAxis: xAxis,
                                yAxis: yAxis,
                                valueYField: `${ks_data[k].label}`,
                                categoryXField: "category"
                             })
                            );

                            series.columns.template.setAll({
                            tooltipText: "{name}: {valueY}",
                            width: am5.percent(100)
                            });
                            series.columns.template.events.on("click",function(ev){
                                if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            series.data.setAll(data);
                        }

                    }else if (item.ks_dashboard_item_type == "ks_radialBar_chart"){
                        for (let k = 0;k<ks_data.length ; k++) {
                            var series = chart.series.push(am5radar.RadarColumnSeries.new(root, {
                                stacked: true,
                                name: `${ks_data[k].label}`,
                                xAxis: xAxis,
                                yAxis: yAxis,
                                valueXField: `${ks_data[k].label}`,
                                categoryYField: "category"
                            }));

                            series.set("stroke",root.interfaceColors.get("background"));
                            series.columns.template.setAll({
                                width: am5.p100,
                                strokeOpacity: 0.1,
                                tooltipText: "{name}: {valueX}  {category}"
                            });
                            series.columns.template.events.on("click",function(ev){
                                if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            series.data.setAll(data);
                        }
                        yAxis.data.setAll(data);
                   }else{
                        for (let k = 0;k<ks_data.length ; k++){
                        var series = chart.series.push(am5radar.RadarLineSeries.new(root, {
                            name:`${ks_data[k].label}`,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueYField: `${ks_data[k].label}`,
                            categoryXField: "category",
                            alignLabels: true,
                            tooltip: am5.Tooltip.new(root, {
                                 labelText: "{valueY}"
                            })

                        }));

                            series.strokes.template.setAll({
                            strokeWidth: 2,

                            });
                        series.bullets.push(function() {
                            var graphics = am5.Circle.new(root, {
                                fill: series.get("fill"),
                                radius: 5
                            });
                            graphics.events.on("click", function(ev) {
                                if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            return am5.Bullet.new(root, {
                                sprite: graphics
                            });
                        });
                        series.data.setAll(data);
                    }
                        xAxis.data.setAll(data);
                   }

                    break;

                case "ks_scatter_chart":
                var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
                 wheelX: "panX",wheelY: "zoomX",layout: root.verticalLayout}));
                    var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
                        renderer: am5xy.AxisRendererX.new(root, { minGridDistance: 50 }),
                        tooltip: am5.Tooltip.new(root, {})
                    }));
                    xAxis.ghostLabel.set("forceHidden", true);

                    var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
                        renderer: am5xy.AxisRendererY.new(root, {}),
                        tooltip: am5.Tooltip.new(root, {})
                    }));
                    yAxis.ghostLabel.set("forceHidden", true);

                    for (let k = 0;k<ks_data.length ; k++){
                        var series = chart.series.push(am5xy.LineSeries.new(root, {
                            name:`${ks_data[k].label}`,
                            name_1 : chart_data.groupby,
                            calculateAggregates: true,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueYField: `${ks_data[k].label}`,
                            valueXField: "category",
                            tooltip: am5.Tooltip.new(root, {
                                 labelText: "{name_1}:{valueX} {name}:{valueY}"
                            })
                        }));

                        series.bullets.push(function() {
                            var graphics = am5.Triangle.new(root, {
                                fill: series.get("fill"),
                                width: 10,
                                height: 7
                            });
                            graphics.events.on("click", function(ev) {
                                if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            return am5.Bullet.new(root, {
                                sprite: graphics
                            });
                        });
                         var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                            behavior: "none",
                            snapToSeries: [series]
                            }));
                            cursor.lineY.set("forceHidden", true);
                            cursor.lineX.set("forceHidden", true);
                        series.strokes.template.set("strokeOpacity", 0);
                        series.data.setAll(data);

                    }
                    break;
            }
                var legend = chart.children.push(
                    am5.Legend.new(root, {
                        centerX: am5.p50,
                        x: am5.p50,
                        layout: root.gridLayout,
                        y: am5.percent(100),
                        centerY: am5.percent(100),
                    })
                );
                if(item.ks_hide_legend == true && series){
                    legend.data.setAll(chart.series.values);
                }


            if (item.ks_data_format && item.ks_data_format == 'global'){
                root.numberFormatter.setAll({
                    numberFormat: "#a",
                    bigNumberPrefixes: [{"number":1e+3,"suffix":"k"},{ "number": 1e+6, "suffix": "M" },
                    { "number": 1e+9, "suffix": "G" },{ "number": 1e+12, "suffix": "T" },
                    { "number": 1e+15, "suffix": "P" },{ "number": 1e+18, "suffix": "E" }]
                });
            }else if (item.ks_data_format && item.ks_data_format == 'indian'){
                root.numberFormatter.setAll({
                    numberFormat: "#a",
                    bigNumberPrefixes: [{"number":1e+3,"suffix":"Th"},{"number":1e+5,"suffix":"Lakh"},
                    { "number": 1e+7, "suffix": "Cr" },{ "number": 1e+9, "suffix": "Arab" }],
                });
            }else if (item.ks_data_format && item.ks_data_format == 'colombian'){
                root.numberFormatter.setAll({
                    numberFormat: "#a",
                    bigNumberPrefixes: [{"number":1e+6,"suffix":"M"},{ "number": 1e+9, "suffix": "M" },{ "number": 1e+12, "suffix": "M" },
                    { "number": 1e+15, "suffix": "M" },{ "number": 1e+18, "suffix": "M" }]
                });
            }else{
                root.numberFormatter.setAll({
                    numberFormat: "#"
                });
            }
            chart.appear(1000, 100);

            if (item.ks_dashboard_item_type != 'ks_pie_chart' &&  item.ks_dashboard_item_type != 'ks_doughnut_chart' && series){
                series.appear();
            }
//            this.chart_container[item.id] = chart;
            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('ks_date_filter_selected');
        }else{
            $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='graph_text'>").text("No Data Available."));
        }
        }else{
         $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='graph_text'>").text("No Data Available."));
        }
    }
     ksrenderfunnelchart($ks_gridstack_container,item){
            var self =this;
            if($ks_gridstack_container.find('.ks_chart_card_body').length){
                var funnelRender = $ks_gridstack_container.find('.ks_chart_card_body');
            }else{
                $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                var funnelRender = $ks_gridstack_container.find('.ks_chart_card_body');
            }
            var funnel_data = JSON.parse(item.ks_chart_data);
            if (funnel_data['labels'] && funnel_data['datasets']){
                var ks_labels = funnel_data['labels'];
                var ks_data = funnel_data.datasets[0].data;
                const ks_sortobj = Object.fromEntries(
                ks_labels.map((key, index) => [key, ks_data[index]]),
                );
                const keyValueArray = Object.entries(ks_sortobj);
                keyValueArray.sort((a, b) => b[1] - a[1]);

                var data=[];
                if (keyValueArray.length){
                    for (let i=0 ; i<keyValueArray.length ; i++){
                    data.push({"stage":keyValueArray[i][0],"applicants":keyValueArray[i][1]})
                    }
                    const root = am5.Root.new(funnelRender[0]);
                    const theme = item.ks_chart_item_color
                    switch(theme){
                    case "default":
                        root.setThemes([am5themes_Animated.new(root)]);
                        break;
                    case "dark":
                        root.setThemes([am5themes_Dataviz.new(root)]);
                        break;
                    case "material":
                        root.setThemes([am5themes_Material.new(root)]);
                        break;
                    case "moonrise":
                        root.setThemes([am5themes_Moonrise.new(root)]);
                        break;
                    };

                    var chart = root.container.children.push(
                        am5percent.SlicedChart.new(root, {
                            layout: root.verticalLayout
                        })
                    );
                    // Create series
                    var series = chart.series.push(
                        am5percent.FunnelSeries.new(root, {
                            alignLabels: false,
                            name: "Series",
                            valueField: "applicants",
                            categoryField: "stage",
                            orientation: "vertical",
                        })
                    );
                    series.data.setAll(data);
                    if(item.ks_show_data_value && item.ks_data_label_type=="value"){
                        series.labels.template.set("text", "{category}: {value}");
                    }else if(item.ks_show_data_value && item.ks_data_label_type=="percent"){
                        series.labels.template.set("text", "{category}: {valuePercentTotal.formatNumber('0.00')}%");
                    }else{
                        series.ticks.template.set("forceHidden", true);
                        series.labels.template.set("forceHidden", true);
                    }
                    var legend = chart.children.push(
                        am5.Legend.new(root, {
                            centerX: am5.p50,
                            x: am5.p50,
                            marginTop: 15,
                            marginBottom: 15
                        })
                    );
                    if(item.ks_hide_legend==true){
                        legend.data.setAll(series.dataItems);
                    }
                    chart.appear(1000, 100);
                    this.chart_container[item.id] = chart;
                    series.slices._values.forEach((rec)=>{
                        rec.events.on("click",function(ev){
                            if (item.ks_data_calculation_type === 'custom' && !self.ks_dashboard_data['ks_ai_dashboard']){
                                self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                            }
                        })
                    })
                }else{
                    $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='funnel_text'>").text("No Data Available."))
                }
            }else{
                    $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='funnel_text'>").text("No Data Available."))
            }
            return $ks_gridstack_container;
     }

     onChartCanvasClick(evt) {

        var self = this;
        this.ksUpdateDashboard = {};
        var item_id = $(evt.target).parent().data().itemId;
//        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_breadcrumb").removeClass("d-none")
        var chart_title = '#'+this.item.name
        if (this.ksUpdateDashboard[item_id]) {
            clearInterval(this.ksUpdateDashboard[item_id]);
            delete self.ksUpdateDashboard[item_id];
        }
        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
        if (self.ks_dashboard_data.ks_item_data[item_id].max_sequnce) {

            var sequence = item_data.sequnce ? item_data.sequnce : 0

            var domain = $(evt.target).parent().data().domain;

            if ($(evt.target).parent().data().last_seq !== sequence) {
                self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
                    model: 'ks_dashboard_ninja.item',
                    method: 'ks_fetch_drill_down_data',
                    args: [item_id, domain, sequence],
                    kwargs : {},
                }).then(function(result) {
                    if (result.ks_list_view_data) {
                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        }
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_title).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        var $container = self.prepare_list(item_data);
                        $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
                    } else {
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        }
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_list_view_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_title).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            self.ksrenderfunnelchart($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                        }else{
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                        self.ks_render_graphs($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data);
                        }

                    }
                });
            }
        }
        evt.stopPropagation();
     }

     async onChartCanvasClick_funnel(evt,item_id,item){
        var self = this;
        this.ksUpdateDashboard = {};
        if (item_id in self.ksUpdateDashboard) {
            clearInterval(self.ksUpdateDashboard[item_id]);
            delete self.ksUpdateDashboard[item_id]
        }
        var domain = [];
        var partner_id;
        var final_active;
//        var myChart = self.chart_container[item_id];
        var index;
        var item_data = self.ks_dashboard_data.ks_item_data[item_id];
        var groupBy = JSON.parse(item_data["ks_chart_data"])['groupby'];
        var labels = JSON.parse(item_data["ks_chart_data"])['labels'];
        var domains = JSON.parse(item_data["ks_chart_data"])['domains'];
        var sequnce = item_data.sequnce ? item_data.sequnce : 0;
//         $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_breadcrumb").removeClass("d-none")
        var chart_title = '#'+item.name
//        if (item.ks_dashboard_item_type == "ks_bullet_chart" || item.ks_dashboard_item_type === "ks_funnel_chart" || item.ks_dashboard_item_type === "ks_flower_view" || item.ks_dashboard_item_type === "ks_radialBar_chart"){
        if (evt.target.dataItem){
            var activePoint = evt.target.dataItem.dataContext;
        }
//        }else{

//            var activePoint = evt.target.dataItem.dataContext;
//        }
        if (activePoint) {
            if (activePoint.category){
                for (let i=0 ; i<labels.length ; i++){
                    if (labels[i] == activePoint.category){
                        index = i
                    }
                }
                domain = domains[index]
            }
            else if (activePoint.stage){
                for (let i=0 ; i<labels.length ; i++){
                    if (labels[i] == activePoint.stage){
                        index = i
                    }
                }
                domain = domains[index]
            }
            if (item_data.max_sequnce != 0 && sequnce < item_data.max_sequnce) {
                self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
                    model: 'ks_dashboard_ninja.item',
                    method: 'ks_fetch_drill_down_data',
                    args: [item_id, domain, sequnce],
                    kwargs : {},
                }).then(function(result) {
                    self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                    self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                    if (result.ks_chart_data) {

                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        }
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_title).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            self.ksrenderfunnelchart($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                        }else{
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            self.ks_render_graphs($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data);
                        }
                    } else {
                        if ('domains' in self.ks_dashboard_data.ks_item_data[item_id]) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        }
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');
                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        self.item = item_data
                        self.prepare_list();
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container).addClass('ks_overflow');
                    }
                });
            } else {
            if (item_data.action) {
                    if (!item_data.ks_is_client_action){
                        var action = Object.assign({}, item_data.action);
                        if (action.view_mode.includes('tree')) action.view_mode = action.view_mode.replace('tree', 'list');
                        for (var i = 0; i < action.views.length; i++) action.views[i][1].includes('tree') ? action.views[i][1] = action.views[i][1].replace('tree', 'list') : action.views[i][1];
                        action['domain'] = domain || [];
                        action['search_view_id'] = [action.search_view_id, 'search']
                    }else{
                        var action = Object.assign({}, item_data.action[0]);
                        if (action.params){
                            action.params.default_active_id || 'mailbox_inbox';
                            }else{
                                action.params = {
                                'default_active_id': 'mailbox_inbox'
                                };
                                action.context = {}
                                action.context.params = {
                                'active_model': false
                                };
                            }
                    }
                } else {
                    var action = {
                        name: _t(item_data.name),
                        type: 'ir.actions.act_window',
                        res_model: item_data.ks_model_name,
                        domain: domain || [],
                        context: {
                            'group_by': groupBy ? groupBy:false ,
                        },
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        view_mode: 'list',
                        target: 'current',
                    }
                }
                if (item_data.ks_show_records) {

                    self.actionService.doAction(action, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                    });
                }
            }
        }
     }

     ksOnDrillUp(e) {
        var self = this;
        var item_id = e.currentTarget.dataset.itemId;
        var item_data = self.ks_dashboard_data.ks_item_data[item_id];
        var domain;
        var chart_name = '#'+item_data.name
        var sequence = parseInt(e.currentTarget.dataset.sequence)
        var chart_id_name =  '#item'+'_' +'-1'
        if(item_data) {

            if ('domains' in item_data) {
                domain = item_data['domains'][sequence+1] ? item_data['domains'][sequence+1] : []
                var sequnce = sequence;
                if (sequnce >= 0) {
                    self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
                        model: 'ks_dashboard_ninja.item',
                        method: 'ks_fetch_drill_down_data',
                        args: [item_id, domain, sequnce],
                        kwargs:{}
                    }).then(function(result) {
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        var id_name = '#'+result.ks_action_name + '_' + sequence;
                        var ks_breadcrumb_elements  = $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).nextAll();
                        if (result.ks_chart_type)  self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
//                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(last_index_id_name).addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        if (result.ks_chart_data) {
                            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
                            ks_breadcrumb_elements.each(function(index,item){
                                $(item).addClass("d-none")
                            })
//                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).addClass('d-none');
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove()
                            if (result.ks_chart_type == "ks_funnel_chart"){
                                self.ksrenderfunnelchart($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                            }else{
                                self.ks_render_graphs($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data);
                            }
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
                            var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                            ks_breadcrumb_elements.each(function(index,item){
                                $(item).addClass("d-none")
                            })
                            self.prepare_list(item_data);
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
                        }

                    });

                } else {
                    var ks_breadcrumb_elements  = $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).nextAll();
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).addClass('d-none');
                    ks_breadcrumb_elements.each(function(index,item){
                        $(item).addClass("d-none")
                    })
                    $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").removeClass("d-none")
                    $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_list_view_heading").removeClass("d-none")
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_name).addClass('d-none');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").addClass('d-none');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").addClass('d-sm-block ');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").removeClass('d-none');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").removeClass('d-none')
                    self.ksFetchChartItem(item_id)
//                        $(self.$el.find('.ks_pager')).removeClass('d-none');
                    var updateValue = self.ks_dashboard_data.ks_set_interval;
                    if (updateValue) {
                        var updateinterval = setInterval(function() {
                            self.ksFetchChartItem(item_id)
                        }, updateValue);
                        self.ksUpdateDashboard[item_id] = updateinterval;
                    }
                }

            } else {
                if(!domain){
                $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").addClass('d-none');
            }

            }
        }

        e.stopPropagation();
    }

    ksFetchChartItem(id) {
        var self = this;
        var item_data = self.ks_dashboard_data.ks_item_data[id];

        return self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_fetch_item",{
            model: 'ks_dashboard_ninja.board',
            method: 'ks_fetch_item',
            args: [
                [item_data.id], self.ks_dashboard_data.ks_dashboard_id, {}
            ],
            kwargs:{},
        }).then(function(new_item_data) {
            this.ks_dashboard_data.ks_item_data[id] = new_item_data[id];
            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + id + "]").children()[0]).find(".card-body").empty();
            var item_data = self.ks_dashboard_data.ks_item_data[id]
            if (item_data.ks_list_view_data) {
                 self.actionService.doAction({
                    type: "ir.actions.client",
                    tag: "reload",
                 });
//                var item_view = $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + id + "]").children()[0]);
//                self.prepare_list();
//                var $textAnswer = $(renderToElement('Ksdashboardlistview', {
//                    list_view_data : this.state.list_view_data,
//                    ks_list_view_type : self.ks_list_view_type,
//                    tmpl_list_type : self.tmpl_list_type,
//                    isDrill : self.isDrill,
//                    ks_breadcrumb : this.ks_breadcrumb
//                }));
//                item_view.find(".card-body").append($container);
//                self.ksFetchChartItem(item_data.item_id)
//                var ks_length = JSON.parse(item_data['ks_list_view_data']).data_rows.length
//                if (new_item_data["ks_list_view_type"] === "ungrouped" && JSON.parse(item_data['ks_list_view_data']).data_rows.length) {
//                    item_view.find('.ks_pager').removeClass('d-none');
//                    if (item.ks_record_count <= item.ks_pagination_limit) item_view.find('.ks_load_next').addClass('ks_event_offer_list');
//                    item_view.find('.ks_value').text("1-" + JSON.parse(item_data['ks_list_view_data']).data_rows.length);
//                } else {
//                    item_view.find('.ks_pager').addClass('d-none');
//                }
            }else if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                self.ksrenderfunnelchart($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data);
            }else{
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                self.ks_render_graphs($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + id + "]"), item_data);
            }
        }.bind(this));
    }


    async ksrendermapview($ks_map_view_tmpl,item){
        console.log("render")
        var self =this;
        if($ks_map_view_tmpl.find('.ks_map_card_body').length){
            var mapRender = $ks_map_view_tmpl.find('.ks_map_card_body');
        }else{
            $($ks_map_view_tmpl.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_map_card_body'>");
            var mapRender = $ks_map_view_tmpl.find('.ks_map_card_body');
        }
        var map_data = JSON.parse(item.ks_chart_data);
        var ks_data=[];
        let data = [];
        let label_data = [];
        let query_label_data = [];
        let domain = [];
        let partner_domain = [];
        var partners = [];
        if (map_data.groupByIds){
            partners = map_data['partner']
        }
        var partners_query = [];
        partners_query = map_data['ks_partners_map']
        var ks_labels = map_data['labels'];
        if (map_data.datasets.length){
            var ks_data = map_data.datasets[0].data;
        }
        if (item.ks_data_calculation_type === 'query'){
            for (let i=0 ; i<ks_labels.length ; i++){
                if (ks_labels[i] !== false){
                    if (typeof ks_labels[i] == 'string'){
                        if (ks_labels[i].includes(',')){
                            ks_labels[i] = ks_labels[i].split(', ')[1]
                        }
                        query_label_data.push(ks_labels[i])
                    }else{
                        query_label_data.push(ks_labels[i])
                    }
                }
            }
            for (let i=0 ; i<query_label_data.length ; i++){
                if (typeof query_label_data[i] == 'string'){
                    for (let j=0 ; j<partners_query.length ; j++){
                        if (query_label_data[i] == partners_query[j].name){
                            data.push({"title":query_label_data[i], "latitude":partners_query[j].partner_latitude, "longitude": partners_query[j].partner_longitude});
                        }
                    }
                }else{
                      data.push({"title":query_label_data[i], "latitude":partners_query[i].partner_latitude, "longitude": partners_query[i].partner_longitude});
                }
            }
        }
        if (ks_data.length && ks_labels.length){
            if (item.ks_data_calculation_type !== 'query'){
                for (let i=0 ; i<ks_labels.length ; i++){
                    if (ks_labels[i] !== false){
                        if (ks_labels[i].includes(',')){
                            ks_labels[i] = ks_labels[i].split(', ')[1]
                        }
                        label_data.push({'title': ks_labels[i], 'value':ks_data[i]})
                    }
                }
                for (let i=0 ; i<label_data.length ; i++){
                    for (let j=0 ; j<partners.length ; j++){
                        if (label_data[i].title == partners[j].name){
                            partners[j].name = partners[j].name + ';' + label_data[i].value
                        }
                    }
                }
                for (let i=0 ; i<partners.length ; i++){
                    data.push({"title":partners[i].name, "latitude":partners[i].partner_latitude, "longitude": partners[i].partner_longitude});
                }
            }
            const root = am5.Root.new(mapRender[0]);
            root.setThemes([am5themes_Animated.new(root)]);

            // Create the map chart
            var chart = root.container.children.push(
              am5map.MapChart.new(root, {
                panX: "translateX",
                panY: "translateY",
                projection: am5map.geoMercator()
              })
            );

            var cont = chart.children.push(
              am5.Container.new(root, {
                layout: root.horizontalLayout,
                x: 20,
                y: 40
              })
            );

            // Add labels and controls
            cont.children.push(
              am5.Label.new(root, {
                centerY: am5.p50,
                text: "Map"
              })
            );

            var switchButton = cont.children.push(
              am5.Button.new(root, {
                themeTags: ["switch"],
                centerY: am5.p50,
                icon: am5.Circle.new(root, {
                  themeTags: ["icon"]
                })
              })
            );

            switchButton.on("active", function() {
              if (!switchButton.get("active")) {
                chart.set("projection", am5map.geoMercator());
                chart.set("panY", "translateY");
                chart.set("rotationY", 0);
                backgroundSeries.mapPolygons.template.set("fillOpacity", 0);
              } else {
                chart.set("projection", am5map.geoOrthographic());
                chart.set("panY", "rotateY");

                backgroundSeries.mapPolygons.template.set("fillOpacity", 0.1);
              }
            });

            cont.children.push(
              am5.Label.new(root, {
                centerY: am5.p50,
                text: "Globe"
              })
            );

            // Create series for background fill
            var backgroundSeries = chart.series.push(am5map.MapPolygonSeries.new(root, {}));
            backgroundSeries.mapPolygons.template.setAll({
              fill: root.interfaceColors.get("alternativeBackground"),
              fillOpacity: 0,
              strokeOpacity: 0
            });

                // Add background polygon
            backgroundSeries.data.push({
              geometry: am5map.getGeoRectangle(90, 180, -90, -180)
            });

            // Create main polygon series for countries
            var polygonSeries = chart.series.push(
              am5map.MapPolygonSeries.new(root, {
                geoJSON: am5geodata_worldLow,
                exclude: ["AQ"]
              })
            );
            polygonSeries.mapPolygons.template.setAll({
              tooltipText: "{name}",
              toggleKey: "active",
              interactive: true
            });

            polygonSeries.mapPolygons.template.states.create("hover", {
              fill: root.interfaceColors.get("primaryButtonHover")
            });

            polygonSeries.mapPolygons.template.states.create("active", {
              fill: root.interfaceColors.get("primaryButtonHover")
            });

            var previousPolygon;

            polygonSeries.mapPolygons.template.on("active", function (active, target) {
              if (previousPolygon && previousPolygon != target) {
                previousPolygon.set("active", false);
              }
              if (target.get("active")) {
                polygonSeries.zoomToDataItem(target.dataItem );
              }
              else {
                chart.goHome();
              }
              previousPolygon = target;
            });

            // Create line series for trajectory lines
            var lineSeries = chart.series.push(am5map.MapLineSeries.new(root, {}));
            lineSeries.mapLines.template.setAll({
              stroke: root.interfaceColors.get("alternativeBackground"),
              strokeOpacity: 0.3
            });

            // Create point series for markers
            var pointSeries = chart.series.push(am5map.MapPointSeries.new(root, {}));
            var colorset = am5.ColorSet.new(root, {});
            const self = root;


            pointSeries.bullets.push(function() {
              var container = am5.Container.new(self, {
                tooltipText: "{title}",
                cursorOverStyle: "pointer"
              });

              var circle = container.children.push(
                am5.Circle.new(self, {
                  radius: 4,
                  tooltipY: 0,
                  fill: colorset.next(),
                  strokeOpacity: 0
                })
              );


              var circle2 = container.children.push(
                am5.Circle.new(self, {
                  radius: 4,
                  tooltipY: 0,
                  fill: colorset.next(),
                  strokeOpacity: 0,
                  tooltipText: "{title}"
                })
              );

              circle.animate({
                key: "scale",
                from: 1,
                to: 5,
                duration: 600,
                easing: am5.ease.out(am5.ease.cubic),
                loops: Infinity
              });

              circle.animate({
                key: "opacity",
                from: 1,
                to: 0.1,
                duration: 600,
                easing: am5.ease.out(am5.ease.cubic),
                loops: Infinity
              });

              return am5.Bullet.new(self, {
                sprite: container
              });
            });

            for (var i = 0; i < data.length; i++) {
              var final_data = data[i];
              addCity(final_data.longitude, final_data.latitude, final_data.title);
            }
            function addCity(longitude, latitude, title) {
              pointSeries.data.push({
                geometry: { type: "Point", coordinates: [longitude, latitude] },
                title: title,
              });
            }

            // Add zoom control
            chart.set("zoomControl", am5map.ZoomControl.new(root, {}));

            // Set clicking on "water" to zoom out
            chart.chartContainer.get("background").events.on("click", function () {
              chart.goHome();
            })

            // Make stuff animate on load
            chart.appear(1000, 100);
            this.chart_container[item.id] = chart;
//                $ks_map_view_tmpl.find('.ks_li_' + item.ks_flower_item_color).addClass('ks_date_filter_selected');
        }else{
            $ks_map_view_tmpl.find('.ks_map_card_body').append($("<div class='map_text'>").text("No Data Available."))
        }
//       }else{
//        $ks_map_view_tmpl.find('.ks_map_card_body').append($("<div class='map_text'>").text("Please select Groupby that has Address."))}
        return $ks_map_view_tmpl;
    }

        ksRenderChartColorOptions(e) {
        var self = this;
        if (!$(e.currentTarget).parent().hasClass('ks_date_filter_selected')) {
            //            FIXME : Correct this later.
            var $parent = $(e.currentTarget).parent().parent();
            $parent.find('.ks_date_filter_selected').removeClass('ks_date_filter_selected')
            $(e.currentTarget).parent().addClass('ks_date_filter_selected')
            var item_data = self.ks_dashboard_data.ks_item_data[$parent.data().itemId];
            var chart_data = JSON.parse(item_data.ks_chart_data);
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/write",{
                    model: 'ks_dashboard_ninja.item',
                    method: 'write',
                    args: [$parent.data().itemId, {
                        "ks_chart_item_color": e.currentTarget.dataset.chartColor
                    }],
                    kwargs:{}
            }).then(function() {
                    self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_chart_item_color'] = e.target.dataset.chartColor;
                    $(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    if (item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                        self.ksrenderfunnelchart($(self.ks_gridstack_container.el),item_data);
                    }else{
                    self.ks_render_graphs($(self.ks_gridstack_container.el),item_data);
                    }
            })
        }
    }

        ksLoadMoreRecords(e) {
            var self = this;
            var ks_intial_count = e.target.parentElement.dataset.prevOffset;
            var ks_offset = e.target.parentElement.dataset.next_offset;
            var itemId = e.currentTarget.dataset.itemId;
            var offset = self.ks_dashboard_data.ks_item_data[itemId].ks_pagination_limit;
            var context = self.ks_dashboard_data['context']

            var params = {};
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_get_list_view_data_offset",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_get_list_view_data_offset',
                args: [parseInt(itemId), {
                    ks_intial_count: ks_intial_count,
                    offset: ks_offset,
                    }, parseInt(self.ks_dashboard_data.ks_dashboard_id), params],
                kwargs:{context:context}
            }).then(function(result) {
                var item_data = self.ks_dashboard_data.ks_item_data[itemId];
                var item_view = $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]");
                self.item.ks_list_view_data = result.ks_list_view_data;
                self.prepare_list();
                $(e.target).parents('.ks_pager').find('.ks_value').text(result.offset + "-" + result.next_offset);
                e.target.parentElement.dataset.next_offset = result.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset;
                $(e.target.parentElement).find('.ks_load_previous').removeClass('ks_event_offer_list');
                if (result.next_offset < parseInt(result.offset) + (offset - 1) || result.next_offset == item_data.ks_record_count || result.next_offset === result.limit){
                    $(e.target).addClass('ks_event_offer_list');
                }
            });
        }

        ksLoadPreviousRecords(e) {
            var self = this;
            var itemId = e.currentTarget.dataset.itemId;
            var offset = self.ks_dashboard_data.ks_item_data[itemId].ks_pagination_limit;
            var ks_offset =  parseInt(e.target.parentElement.dataset.prevOffset) - (offset + 1) ;
            var ks_intial_count = e.target.parentElement.dataset.next_offset;
            var context = self.ks_dashboard_data['context']
            var params = {};
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_get_list_view_data_offset",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_get_list_view_data_offset',
//                context: self.getContext(),
                args: [parseInt(itemId), {
                    ks_intial_count: ks_intial_count,
                    offset: ks_offset,
                    }, parseInt(self.ks_dashboard_data.ks_dashboard_id), params],
                kwargs:{context:context}
            }).then(function(result) {
                var item_data = self.ks_dashboard_data.ks_item_data[itemId];
                var item_view = $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]");
                self.item.ks_list_view_data = result.ks_list_view_data;
                self.prepare_list();
                $(e.target).parents('.ks_pager').find('.ks_value').text(result.offset + "-" + result.next_offset);
                e.target.parentElement.dataset.next_offset = result.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset;
                $(e.target.parentElement).find('.ks_load_next').removeClass('ks_event_offer_list');
                if (result.offset === 1) {
                    $(e.target).addClass('ks_event_offer_list');
                }
            });
        }

        ksOnListItemInfoClick(e) {
            var self = this;
            var item_id = e.currentTarget.dataset.itemId;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var action = {
                name: _t(item_data.name),
                type: 'ir.actions.act_window',
                res_model: e.currentTarget.dataset.model,
                domain: item_data.ks_domain || [],
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
            }
            if (e.currentTarget.dataset.listViewType === "ungrouped") {
                action['view_mode'] = 'form';
                action['views'] = [
                    [false, 'form']
                ];
                action['res_id'] = parseInt(e.currentTarget.dataset.recordId);
            } else {
                if (e.currentTarget.dataset.listType === "date_type") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['domain'] = domain;
                } else if (e.currentTarget.dataset.listType === "relational_type") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['domain'] = domain;
                    action['context']['search_default_' + e.currentTarget.dataset.groupby] = parseInt(e.currentTarget.dataset.recordId);
                } else if (e.currentTarget.dataset.listType === "other") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['context']['search_default_' + e.currentTarget.dataset.groupby] = parseInt(e.currentTarget.dataset.recordId);
                    action['domain'] = domain;
                }
            }
            self.actionService.doAction(action)
        }

};

Ksdashboardgraph.props = {
    item: { type: Object, Optional:true},
    dashboard_data: { type: Object, Optional:true},
    ksdatefilter : {type: String ,Optional:true},
    pre_defined_filter :{type:Object, Optional:true}
};

Ksdashboardgraph.template = "Ks_chart_list_container";
