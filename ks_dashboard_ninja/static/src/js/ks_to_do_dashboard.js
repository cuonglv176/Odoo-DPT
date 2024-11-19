odoo.define('ks_dashboard_ninja.ks_to_do_dashboard_filter', function (require) {
"use strict";

var KsDashboard = require('ks_dashboard_ninja.ks_dashboard');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;
var Dialog = require('web.Dialog');
var config = require('web.config');

return KsDashboard.include({
         events: _.extend({}, KsDashboard.prototype.events, {
        'click .ks_edit_content': '_onKsEditTask',
        'click .ks_delete_content': '_onKsDeleteContent',
        'click .header_add_btn': '_onKsAddTask',
        'click .ks_create_task': '_onKsCreateTask',
//        'click .ks_add_section': '_onKsAddSection',
        'click .ks_li_tab': '_onKsUpdateAddButtonAttribute',
        'click .ks_do_item_active_handler': '_onKsActiveHandler',
        'click .ks_li_tab': 'ksOnToDoClick',
//        'click .ks_edit_map_form': 'ksOpenForm'
    }),

        ksOnToDoClick: function(ev){
            ev.preventDefault();
            var self= this;
            var tab_id = $(ev.currentTarget).attr('href');
            var $tab_section = $('#' + tab_id.substring(1));
            $(ev.currentTarget).addClass("active");
            $(ev.currentTarget).parent().siblings().each(function(){
                $(this).children().removeClass("active");
            });
            $('#' + tab_id.substring(1)).siblings().each(function(){
                $(this).removeClass("active");
                $(this).addClass("fade");
            });
            $tab_section.removeClass("fade");
            $tab_section.addClass("active");
            $(ev.currentTarget).parent().parent().siblings().attr('data-section-id', $(ev.currentTarget).data().sectionId);
        },

        ksRenderDashboardItems: function(items) {
            var self = this;
            self.$el.find('.print-dashboard-btn').addClass("ks_pro_print_hide");
            if (self.ks_dashboard_data.ks_gridstack_config) {
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
            }
            var item_view;
            var ks_container_class = 'grid-stack-item',
                ks_inner_container_class = 'grid-stack-item-content';
                for (var i = 0; i < items.length; i++) {
                if (self.grid) {

                    if (items[i].ks_dashboard_item_type === 'ks_tile') {
                        var item_view = self._ksRenderDashboardTile(items[i])
                        if (items[i].id in self.gridstackConfig) {
                             if (config.device.isMobile){
                                self.grid.addWidget($(item_view)[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:true,minW:2,maxW:null,minH:2,maxH:2,id:items[i].id,});
                             }
                             else{
                                self.grid.addWidget($(item_view)[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:false,minW:2,maxW:null,minH:2,maxH:2,id:items[i].id,});
                             }
                        } else {
                             self.grid.addWidget($(item_view)[0], {x:0, y:0, w:3, h:2,autoPosition:true,minW:2,maxW:null,minH:2,maxH:2,id:items[i].id});
                        }
                    } else if (items[i].ks_dashboard_item_type === 'ks_list_view') {
                        self._renderListView(items[i], self.grid)
                    } else if (items[i].ks_dashboard_item_type === 'ks_kpi') {
                        var $kpi_preview = self.renderKpi(items[i], self.grid)
                        if (items[i].id in self.gridstackConfig) {
                            if (config.device.isMobile){
                                self.grid.addWidget($kpi_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:true,minW:2,maxW:null,minH:2,maxH:3,id:items[i].id});
                             }
                             else{
                                self.grid.addWidget($kpi_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h,autoPosition:false,minW:2,maxW:null,minH:2,maxH:3,id:items[i].id});
                             }
                        } else {
                             self.grid.addWidget($kpi_preview[0], {x:0, y:0, w:3, h:2,autoPosition:true,minW:2,maxW:null,minH:2,maxH:3,id:items[i].id});
                        }

                    }  else if (items[i].ks_dashboard_item_type === 'ks_to_do'){
                        var $to_do_preview = self.ksRenderToDoDashboardView(items[i])[0];
                        if (items[i].id in self.gridstackConfig) {
                            if (config.device.isMobile){
                                self.grid.addWidget($to_do_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h, autoPosition:true, minW:5, maxW:null, minH:2, maxH:null, id:items[i].id});
                             }
                             else{
                                self.grid.addWidget($to_do_preview[0], {x:self.gridstackConfig[items[i].id].x, y:self.gridstackConfig[items[i].id].y, w:self.gridstackConfig[items[i].id].w, h:self.gridstackConfig[items[i].id].h, autoPosition:false, minW:5, maxW:null, minH:2, maxH:null, id:items[i].id});
                             }
                        } else {
                            self.grid.addWidget($to_do_preview[0], {x:0, y:0, w:6, h:4, autoPosition:true, minW:5, maxW:null, minH:2, maxH:null, id:items[i].id})
                        }
                    } else if(items[i].ks_dashboard_item_type === 'ks_flower_view'){
                        self._ksflowerchart(items[i], self.grid)
                    } else if(items[i].ks_dashboard_item_type === 'ks_radialBar_chart'){
                        self._renderradialchart(items[i], self.grid)
                    } else if (items[i].ks_dashboard_item_type === 'ks_map_view') {
                        self._renderMap(items[i], self.grid)
                    }else if(items[i].ks_dashboard_item_type === 'ks_funnel_chart' || items[i].ks_dashboard_item_type === 'ks_bullet_chart'){
                        self._ksfunnelchart(items[i],self.grid)
                   }else{
                        self._renderGraph(items[i], self.grid)
                    }
                }
            }
        },

        ksRenderToDoDashboardView: function(item){
            var self = this;
            var item_title = item.name;
            var item_id = item.id;
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
            var list_to_do_data = JSON.parse(item.ks_to_do_data)
            var ks_header_color = self._ks_get_rgba_format(item.ks_header_bg_color);
            var ks_font_color = self._ks_get_rgba_format(item.ks_font_color);
            var ks_rgba_button_color = self._ks_get_rgba_format(item.ks_button_color);
            var $ksItemContainer = self.ksRenderToDoView(item);
            var $ks_gridstack_container = $(QWeb.render('ks_to_do_dashboard_container', {
                ks_chart_title: item_title,
                ksIsDashboardManager: self.ks_dashboard_data.ks_dashboard_manager,
                ksIsUser: true,
                ks_dashboard_list: self.ks_dashboard_data.ks_dashboard_list,
                item_id: item_id,
                to_do_view_data: list_to_do_data,
                ks_rgba_button_color:ks_rgba_button_color,
                ks_info: ks_description,
                ks_company:item.ks_company
            })).addClass('ks_dashboarditem_id')
            $ks_gridstack_container.find('.ks_card_header').addClass('ks_bg_to_color').css({"background-color": ks_header_color });
            $ks_gridstack_container.find('.ks_card_header').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
            $ks_gridstack_container.find('.ks_li_tab').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
            $ks_gridstack_container.find('.ks_list_view_heading').addClass('ks_bg_to_color').css({"color": ks_font_color + ' !important' });
            $ks_gridstack_container.find('.ks_to_do_card_body').append($ksItemContainer)
            return [$ks_gridstack_container, $ksItemContainer];
        },

        ksRenderToDoView: function(item, ks_tv_play=false) {
            var self = this;
            var  item_id = item.id;
            var list_to_do_data = JSON.parse(item.ks_to_do_data);
            var $todoViewContainer = $(QWeb.render('ks_to_do_dashboard_inner_container', {
                ks_to_do_view_name: "Test",
                to_do_view_data: list_to_do_data,
                item_id: item_id,
                ks_tv_play: ks_tv_play
            }));

            return $todoViewContainer
        },

//        _onKsCreateTask

        _onKsEditTask: function(e){
            var self = this;
            var ks_description_id = e.currentTarget.dataset.contentId;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var ks_section_id = e.currentTarget.dataset.sectionId;
            var ks_description = $(e.currentTarget.parentElement.parentElement).find('.ks_description').attr('value');

            var $content = "<div><input type='text' class='ks_description' value='"+ ks_description +"' placeholder='Task'></input></div>"
            var dialog = new Dialog(this, {
            title: _t('Edit Task'),
            size: 'medium',
            $content: $content,
            buttons: [
                {
                text: 'Save',
                classes: 'btn-primary',
                click: function(e){
                    var content = $(e.currentTarget.parentElement.parentElement).find('.ks_description').val();
                    if (content.length === 0){
                        content = ks_description;
                    }
                    self.onSaveTask(content, parseInt(ks_description_id), parseInt(ks_item_id), parseInt(ks_section_id));
                },
                close: true,
            },
            {
                    text: _t('Close'),
                    classes: 'btn-secondary o_form_button_cancel',
                    close: true,
                }
            ],
        });
            dialog.open();
        },

        onSaveTask: function(content, ks_description_id, ks_item_id, ks_section_id){
            var self = this;
            this._rpc({
                    model: 'ks_to.do.description',
                    method: 'write',
                    args: [ks_description_id, {
                        "ks_description": content
                    }],
                }).then(function() {
                    self.ksFetchUpdateItem(ks_item_id).then(function(){
                        $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                        $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                    });
                });
        },

        _onKsDeleteContent: function(e){
            var self = this;
            var ks_description_id = e.currentTarget.dataset.contentId;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var ks_section_id = e.currentTarget.dataset.sectionId;

            Dialog.confirm(this, (_t("Are you sure you want to remove this task?")), {
                confirm_callback: function() {

                    self._rpc({
                    model: 'ks_to.do.description',
                    method: 'unlink',
                    args: [parseInt(ks_description_id)],
                }).then(function() {
                        self.ksFetchUpdateItem(ks_item_id).then(function(){
                            $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                            $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                            $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                            $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                            $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                            $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                            $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                        });
                    });
                },
            });
        },

        _onKsAddTask: function(e){
            var self = this;
            var ks_section_id = e.currentTarget.dataset.sectionId;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var $content = "<div><input type='text' class='ks_section' placeholder='Task' required></input></div>"
            var dialog = new Dialog(this, {
            title: _t('New Task'),
            $content: $content,
            size: 'medium',
            buttons: [
                {
                text: 'Save',
                classes: 'btn-primary ks_create_task',
                click: function(e){
                    var content = $(e.currentTarget.parentElement.parentElement).find('.ks_section').val();
                    if (content.length === 0){

//                        this.do_notify(false, _t('Successfully sent to printer!'));
                    }
                    else{
                        self._onCreateTask(content, parseInt(ks_section_id), parseInt(ks_item_id));
                    }
                },
                close: true,
            },
            {
                    text: _t('Close'),
                    classes: 'btn-secondary o_form_button_cancel',
                    close: true,
                }
            ],
        });
            dialog.open();
        },

        _onCreateTask: function(content, ks_section_id, ks_item_id){
            var self = this;
            this._rpc({
                    model: 'ks_to.do.description',
                    method: 'create',
                    args: [{
                        ks_to_do_header_id: ks_section_id,
                        ks_description: content,
                    }],
                }).then(function() {
                    self.ksFetchUpdateItem(ks_item_id).then(function(){
                        $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                        $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                    });

                });
        },

        _onKsUpdateAddButtonAttribute: function(e){
            var item_id = e.currentTarget.dataset.itemId;
            var sectionId = e.currentTarget.dataset.sectionId;
            $(".header_add_btn[data-item-id=" + item_id + "]").attr('data-section-id', sectionId);
        },

        _onKsActiveHandler: function(e){
            var self = this;
            var ks_item_id = e.currentTarget.dataset.itemId;
            var content_id = e.currentTarget.dataset.contentId;
            var ks_task_id = e.currentTarget.dataset.contentId;
            var ks_section_id = e.currentTarget.dataset.sectionId;
            var ks_value = e.currentTarget.dataset.valueId;
            if (ks_value== 'True'){
                ks_value = false
            }else{
                ks_value = true
            }
            self.content_id = parseInt(content_id);
            this._rpc({
                    model: 'ks_to.do.description',
                    method: 'write',
                    args: [parseInt(content_id), {
                        "ks_active": ks_value
                    }],
                }).then(function() {
                    self.ksFetchUpdateItem(ks_item_id).then(function(){
                        $(".ks_li_tab[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_li_tab[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('active');
                        $(".ks_tab_section[data-item-id=" + ks_item_id + "]").removeClass('show');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('active');
                        $(".ks_tab_section[data-section-id=" + ks_section_id + "]").addClass('show');
                        $(".header_add_btn[data-item-id=" + ks_item_id + "]").attr('data-section-id', ks_section_id);
                    });
                });
        },

        ks_radial_container_option: function(chart_title, ksIsDashboardManager, ksIsUser, ks_dashboard_list, chart_id, ks_info, ksChartColorOptions, ks_company, ks_dashboard_item_type){
            var container_data = {
                ks_chart_title: chart_title,
                ksIsDashboardManager: ksIsDashboardManager,
                ksIsUser:ksIsUser,
                ks_dashboard_list: ks_dashboard_list,
                chart_id: chart_id,
                ks_info:ks_info,
                ksChartColorOptions: ksChartColorOptions,
                ks_company:ks_company,
                ks_dashboard_item_type:ks_dashboard_item_type,
            }
            return container_data;
        },

        _renderradialchart: function (item) {
            var self = this;
            var isDrill = item.isDrill ? item.isDrill : false;
            this.chart
            this.ksColorOptions = ["default","dark","moonrise","material"]
            var chart_id = item.id;
            var radial_title = item.name;
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
            var container_data = self.ks_radial_container_option(radial_title, self.ks_dashboard_data.ks_dashboard_manager, true, self.ks_dashboard_data.ks_dashboard_list, chart_id, ks_description, this.ksColorOptions, item.ks_company,item.ks_dashboard_item_type);

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_container', container_data)).addClass('ks_dashboarditem_id');
            $ks_gridstack_container.find(".ks_dashboard_item_button_container").addClass("ks_radial_item_container");
            var ksLayoutGridId = $(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id')
            if(ksLayoutGridId && ksLayoutGridId != 'ks_default'){
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_child_boards[parseInt(ksLayoutGridId)][1])
            }

            parseInt($(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id'))
            if (chart_id in self.gridstackConfig) {
               if (config.device.isMobile){
                   self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:true,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
               }
               else{
                   self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:false,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
               }
            } else {
                 self.grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:5, h:4,autoPosition:true,minW:4,maxW:null,minH:3,maxH:null, id :chart_id});
            }
            self.ksrenderradialchart($ks_gridstack_container,item);
        },
        ksrenderradialchart($ks_gridstack_container,item){
           var self =this;
           if($ks_gridstack_container.find('.ks_chart_card_body').length){
                var radialRender = $ks_gridstack_container.find('.ks_chart_card_body');
           }else{
                $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                var radialRender = $ks_gridstack_container.find('.ks_chart_card_body');
           }
           var radial_data = JSON.parse(item.ks_chart_data);
           var ks_labels = radial_data['labels'];
           var ks_data=[];
           let data = [];
           if (radial_data.datasets){
               for (let i=0 ; i<radial_data.datasets.length ; i++){
                    ks_data.push({"ks_data":radial_data.datasets[i].data});
               }
           }
           if (ks_data.length && ks_labels.length){
                for (let i=0 ; i<radial_data.datasets.length ; i++){
                    ks_data.push({"ks_data":radial_data.datasets[i].data});
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
                const root = am5.Root.new(radialRender[0]);
                const theme = item.ks_radial_item_color
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

                // Create chart
                var chart = root.container.children.push(am5radar.RadarChart.new(root, {
                  panX: false,
                  panY: false,
                  wheelX: "panX",
                  wheelY: "zoomX",
                }));

                // Add cursor
//                var cursor = chart.set("cursor", am5radar.RadarCursor.new(root, {
//                  behavior: "zoomX"
//                }));
//
//                cursor.lineY.set("visible", false);

                // Create axes and their renderers
                var xRenderer = am5radar.AxisRendererCircular.new(root, {
                  strokeOpacity: 0.1,
                  minGridDistance: 50
                });

                xRenderer.labels.template.setAll({
                  radius: 23,
                  maxPosition: 0.98
                });

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

                // Create series
                for (var i = 0; i <radial_data.datasets.length; i++) {
                  var series = chart.series.push(am5radar.RadarColumnSeries.new(root, {
                    stacked: true,
                    name: `${radial_data.datasets[i].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueXField: `value${i+1}`,
                    categoryYField: "category"
                  }));

                  series.set("stroke",root.interfaceColors.get("background"));
                  series.columns.template.setAll({
                    width: am5.p100,
                    strokeOpacity: 0.1,
                    tooltipText: "{name}: {valueX}  {category}"
                  });

                  series.data.setAll(data);
                  series.appear(1000);
                }
                var legend = chart.children.push(
                    am5.Legend.new(root, {
                        centerX: am5.percent(100),
                        x: am5.percent(100),
                        layout: root.verticalLayout
                    })
                );

                if(item.ks_hide_legend==true){
                    legend.data.setAll(chart.series.values);
                }

                yAxis.data.setAll(data);

                // Animate chart and series in
                chart.appear(1000, 100);
                this.chart_container[item.id] = chart;
                $ks_gridstack_container.find('.ks_li_' + item.ks_radial_item_color).addClass('ks_date_filter_selected');
                series.columns.template.events.on("click",function(ev){
                    if (item.ks_data_calculation_type === 'custom'){
                        self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                    }
                });
           }else{
                $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='radial_text'>").text("No Data Available."))
           }
            return $ks_gridstack_container;
        },

        _ksflowerchart:function(item){
            var self = this;
            var isDrill = item.isDrill ? item.isDrill : false;
            this.chart
            this.ksColorOptions = ["default","dark","moonrise","material"]
            var chart_id = item.id;
            var flower_title = item.name;
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
            var container_data = this.ks_flower_container_option(flower_title, self.ks_dashboard_data.ks_dashboard_manager, true, self.ks_dashboard_data.ks_dashboard_list, chart_id, ks_description, this.ksColorOptions, item.ks_company,item.ks_dashboard_item_type);

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_container', container_data)).addClass('ks_dashboarditem_id');
            $ks_gridstack_container.find(".ks_dashboard_item_button_container").addClass("ks_flower_item_container");
            var ksLayoutGridId = $(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id')
            if(ksLayoutGridId && ksLayoutGridId != 'ks_default'){
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_child_boards[parseInt(ksLayoutGridId)][1])
            }
            parseInt($(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id'))
            if (chart_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:true,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
                else{
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:false,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
            } else {
                  self.grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:5, h:4,autoPosition:true,minW:4,maxW:null,minH:3,maxH:null, id :chart_id});
            }
            self.ksrenderflowerchart($ks_gridstack_container,item);
        },
        ksrenderflowerchart($ks_gridstack_container,item){
            var self =this;
            if($ks_gridstack_container.find('.ks_chart_card_body').length){
                var flowerRender = $ks_gridstack_container.find('.ks_chart_card_body');
            }else{
                $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                var flowerRender = $ks_gridstack_container.find('.ks_chart_card_body');
            }
            var flower_data = JSON.parse(item.ks_chart_data);
            var ks_labels = flower_data['labels'];
            var ks_data=[];
            let data = [];
            if (flower_data.datasets){
                for (let i=0 ; i<flower_data.datasets.length ; i++){
                    ks_data.push({"ks_data":flower_data.datasets[i].data});
                }
            }
            if (ks_data.length && ks_labels.length){
                for (let i=0 ; i<flower_data.datasets.length ; i++){
                    ks_data.push({"ks_data":flower_data.datasets[i].data});
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
                const root = am5.Root.new(flowerRender[0]);
                const theme = item.ks_flower_item_color
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
                  am5radar.RadarChart.new(root, {
                    wheelY: "zoomX",
                    wheelX: "panX",
                    panX: false,
                    panY: false,
                    })
                );

//                 // Add cursor
                var cursor = chart.set("cursor", am5radar.RadarCursor.new(root, {
                  behavior: "zoomX"
                }));

                cursor.lineY.set("visible", false);

                 // Create axes and their renderers
                var xRenderer = am5radar.AxisRendererCircular.new(root, {
                  cellStartLocation: 0.2,
                  cellEndLocation: 0.8
                });

                xRenderer.labels.template.setAll({
                  radius: 23
                });

                var xAxis = chart.xAxes.push(
                  am5xy.CategoryAxis.new(root, {
                    maxDeviation: 0,
                    categoryField: "category",
                    renderer: xRenderer,
                    tooltip: am5.Tooltip.new(root, {})
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
                  am5xy.ValueAxis.new(root, {
                    renderer: am5radar.AxisRendererRadial.new(root, {})
                  })
                );

                 // Create series
                for (var i = 0; i <flower_data.datasets.length ; i++) {
                  var series = chart.series.push(
                    am5radar.RadarColumnSeries.new(root, {
                      name: `${flower_data.datasets[i].label}`,
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
                    am5.Legend.new(root, {
                        centerX: am5.percent(100),
                        x: am5.percent(100),
                        layout: root.verticalLayout
                    })
                );

                if(item.ks_hide_legend==true){
                    legend.data.setAll(chart.series.values);
                }

                chart.appear(1000, 100);
                this.chart_container[item.id] = chart;
                $ks_gridstack_container.find('.ks_li_' + item.ks_flower_item_color).addClass('ks_date_filter_selected');
                series.columns.template.events.on("click",function(ev){
                    if (item.ks_data_calculation_type === 'custom'){
                        self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                    }
                });
            }else{
                $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='flower_text'>").text("No Data Available."))
            }
            return $ks_gridstack_container;
        },

        ks_flower_container_option: function(chart_title, ksIsDashboardManager, ksIsUser, ks_dashboard_list, chart_id, ks_info, ksChartColorOptions, ks_company,ks_dashboard_item_type){
            var container_data = {
                ks_chart_title: chart_title,
                ksIsDashboardManager: ksIsDashboardManager,
                ksIsUser:ksIsUser,
                ks_dashboard_list: ks_dashboard_list,
                chart_id: chart_id,
                ks_info:ks_info,
                ksChartColorOptions: ksChartColorOptions,
                ks_company:ks_company,
                ks_dashboard_item_type:ks_dashboard_item_type
            }
            return container_data;
        },

        _renderMap: function (item) {
            var self = this;
            var isDrill = item.isDrill ? item.isDrill : false;
            this.chart
            var map_title = item.name;
            var map_id = item.id;
            if (item.ks_info){
                var ks_description = item.ks_info.split('\n');
                var ks_description = ks_description.filter(element => element !== '')
            }else {
                var ks_description = false;
            }
            var container_data = this.ks_map_container_option(map_title, self.ks_dashboard_data.ks_dashboard_manager, true, self.ks_dashboard_data.ks_dashboard_list, map_id, ks_description, item.ks_company, item.ks_dashboard_item_type)
            var $ks_map_view_tmpl = $(QWeb.render('ks_map_view_tmpl', container_data)).addClass('ks_dashboarditem_id');
            $ks_map_view_tmpl.find(".ks_dashboard_item_button_container").addClass("ks_map_item_container");
            var ksLayoutGridId = $(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id')
            if(ksLayoutGridId && ksLayoutGridId != 'ks_default'){
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_child_boards[parseInt(ksLayoutGridId)][1])
            }
            parseInt($(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id'))
            if (map_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    self.grid.addWidget($ks_map_view_tmpl[0], {x:self.gridstackConfig[map_id].x, y:self.gridstackConfig[map_id].y, w:self.gridstackConfig[map_id].w, h:self.gridstackConfig[map_id].h, autoPosition:true,minW:4,maxW:null,minH:3,maxH:null,id :map_id});
                }
                else{
                    self.grid.addWidget($ks_map_view_tmpl[0], {x:self.gridstackConfig[map_id].x, y:self.gridstackConfig[map_id].y, w:self.gridstackConfig[map_id].w, h:self.gridstackConfig[map_id].h, autoPosition:false,minW:5,maxW:null,minH:3,maxH:null,id :map_id});
                }
            } else {
                  self.grid.addWidget($ks_map_view_tmpl[0], {x:0, y:0, w:5, h:4,autoPosition:true,minW:5,maxW:null,minH:3,maxH:null, id :map_id});
            }
            self.ksrendermapview($ks_map_view_tmpl,item);
        },

        async ksrendermapview($ks_map_view_tmpl,item){
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
                domain = [['id', 'in', map_data.groupByIds]]
                const fields = ["partner_latitude", "partner_longitude", "name"];
                await this._rpc({
                    model: 'res.partner',
                    method: 'search_read',
                    args: [domain, fields],
                }).then( (records) => {
                    partners = records;
                });
//                partners = await this.orm.searchRead("res.partner", domain, fields);
            }
            if ( item.ks_partners_map ) {
                partner_domain = [['id', 'in', JSON.parse(item.ks_partners_map)]]
            }
            var partners_query = [];
            const fields = ["partner_latitude", "partner_longitude", "name"];
            await this._rpc({
                model: 'res.partner',
                method: 'search_read',
                args: [partner_domain, fields],
            }).then( (records) => {
                partners_query = records;
            });
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
            return $ks_map_view_tmpl;
        },

        ks_map_container_option: function(map_title, ksIsDashboardManager, ksIsUser, ks_dashboard_list, map_id, ks_info, ks_company, ks_dashboard_item_type){
            var container_data = {
                ks_map_title: map_title,
                ksIsDashboardManager: ksIsDashboardManager,
                ksIsUser:ksIsUser,
                ks_dashboard_list: ks_dashboard_list,
                map_id: map_id,
                ks_info:ks_info,
                ks_company:ks_company,
                ks_dashboard_item_type:ks_dashboard_item_type
            }
            return container_data;
        },

//        ksOpenForm: function(e) {
//            var self = this;
//            var itemId = parseInt(e.currentTarget.dataset.itemId);
//            if (itemId){
//                self.do_action({
//                    type: 'ir.actions.act_window',
//                    res_model: 'ks_dashboard_ninja.item',
//                    res_id: itemId,
//                    view_id: 'ks_dashboard_ninja_list_form_view',
//                    views: [
//                        [false, 'form']
//                    ],
//                    target: 'current',
//                });
//            }
//        },
        ks_funnel_container_option: function(chart_title, ksIsDashboardManager, ksIsUser, ks_dashboard_list, chart_id, ks_info, ksChartColorOptions, ks_company,ks_dashboard_item_type){
            var container_data = {
                ks_chart_title: chart_title,
                ksIsDashboardManager: ksIsDashboardManager,
                ksIsUser:ksIsUser,
                ks_dashboard_list: ks_dashboard_list,
                chart_id: chart_id,
                ks_info:ks_info,
                ksChartColorOptions: ksChartColorOptions,
                ks_company:ks_company,
                ks_dashboard_item_type:ks_dashboard_item_type
            }
            return container_data;
        },
        _ksfunnelchart:function(item){
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
            var container_data = this.ks_funnel_container_option(funnel_title, self.ks_dashboard_data.ks_dashboard_manager, true, self.ks_dashboard_data.ks_dashboard_list, chart_id, ks_description, this.ksColorOptions,item.ks_company,item.ks_dashboard_item_type);

            var $ks_gridstack_container = $(QWeb.render('ks_gridstack_container', container_data)).addClass('ks_dashboarditem_id');
            $ks_gridstack_container.find(".ks_dashboard_item_button_container").addClass("ks_funnel_item_container");
            var ksLayoutGridId = $(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id');
            if(ksLayoutGridId && ksLayoutGridId != 'ks_default'){
                self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_child_boards[parseInt(ksLayoutGridId)][1])
            }
            parseInt($(self.$el[0]).find('.ks_layout_selected').attr('data-ks_layout_id'))
            if (chart_id in self.gridstackConfig) {
                if (config.device.isMobile){
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:true,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
                else{
                    self.grid.addWidget($ks_gridstack_container[0], {x:self.gridstackConfig[chart_id].x, y:self.gridstackConfig[chart_id].y, w:self.gridstackConfig[chart_id].w, h:self.gridstackConfig[chart_id].h, autoPosition:false,minW:4,maxW:null,minH:3,maxH:null,id :chart_id});
                }
            } else {
                  self.grid.addWidget($ks_gridstack_container[0], {x:0, y:0, w:5, h:4,autoPosition:true,minW:4,maxW:null,minH:3,maxH:null, id :chart_id});
            }
            if (item.ks_dashboard_item_type =="ks_funnel_chart"){
                self.ksrenderfunnelchart($ks_gridstack_container,item);
            }else if(item.ks_dashboard_item_type =="ks_bullet_chart"){
                self.ksrenderbulletchart($ks_gridstack_container,item)
            }
        },
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
                    const theme = item.ks_funnel_item_color
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
                    $ks_gridstack_container.find('.ks_li_' + item.ks_funnel_item_color).addClass('ks_date_filter_selected');
                    series.slices._values.forEach((rec)=>{
                        rec.events.on("click",function(ev){
                            if (item.ks_data_calculation_type === 'custom'){
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
        },

         ksrenderbulletchart($ks_gridstack_container,item){
            var self =this;
            if($ks_gridstack_container.find('.ks_chart_card_body').length){
                var funnelRender = $ks_gridstack_container.find('.ks_chart_card_body');
            }else{
                $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                var funnelRender = $ks_gridstack_container.find('.ks_chart_card_body');
            }
            var funnel_data = JSON.parse(item.ks_chart_data);
            var ks_labels = funnel_data['labels'];
            var ks_data = funnel_data.datasets;
            var data=[];
            if (ks_data.length && ks_labels.length){
                for (let i=0 ; i<ks_labels.length ; i++){
                    let data2={};
                    for (let j=0 ;j<ks_data.length ; j++){
                        data2[`value${j+1}`] = ks_data[j].data[i]
                    }
                    data2["category"] = ks_labels[i]
                    data.push(data2)
                }
                const root = am5.Root.new(funnelRender[0]);
                const theme = item.ks_funnel_item_color
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

                var chart = root.container.children.push(am5xy.XYChart.new(root, {
                panX: true,
                panY: false,
                wheelX: "panX",
                wheelY: "zoomX",
                layout: root.verticalLayout
                }));

                var xRenderer = am5xy.AxisRendererX.new(root, {
                minGridDistance: 70
                });

                var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
                categoryField: "category",
                renderer: xRenderer,
                tooltip: am5.Tooltip.new(root, {
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

                var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
                min: 0,
                renderer: am5xy.AxisRendererY.new(root, {
                strokeOpacity: 0.1
                })
                }));

                for (let k = 0;k<ks_data.length ; k++){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                    name: `${ks_data[k].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueYField:`value${k+1}`,
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
                    series.data.setAll(data);
                }

                var legend = chart.children.unshift(am5.Legend.new(root, {
                centerX: am5.p50,
                x: am5.p50,
                marginTop: 15,
                marginBottom: 15
                }));
                if(item.ks_hide_legend==true){
                legend.data.setAll(chart.series.values);
                }

                if (item.ks_show_data_value == true){
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
                }
                var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                    behavior: "none"
                    })
                );
                cursor.lineY.set("visible", false);
                cursor.lineX.set("visible", false);


                chart.appear(1000, 100);
                series.appear();
                this.chart_container[item.id] = chart;
                $ks_gridstack_container.find('.ks_li_' + item.ks_funnel_item_color).addClass('ks_date_filter_selected');
                series.columns.template.events.on("click",function(ev){
                    if (item.ks_data_calculation_type === 'custom'){
                        self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                    }
                });
            }else{
                $ks_gridstack_container.find('.ks_chart_card_body').append($("<div class='funnel_text'>").text("No Data Available."))
            }
            return $ks_gridstack_container;
         },

        async onChartCanvasClick_funnel(evt,item_id,item){
            var self = this;
            if (item_id in self.ksUpdateDashboard) {
                clearInterval(self.ksUpdateDashboard[item_id]);
                delete self.ksUpdateDashboard[item_id]
            }
            var domain = [];
            var partner_id;
            var final_active;
            var myChart = self.chart_container[item_id];
            var index;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var groupBy = JSON.parse(item_data["ks_chart_data"])['groupby'];
            var labels = JSON.parse(item_data["ks_chart_data"])['labels'];
            var domains = JSON.parse(item_data["ks_chart_data"])['domains'];
            var sequnce = item_data.sequnce ? item_data.sequnce : 0;
            if (item.ks_dashboard_item_type == "ks_bullet_chart" || item.ks_dashboard_item_type === "ks_funnel_chart" || item.ks_dashboard_item_type === "ks_flower_view" || item.ks_dashboard_item_type === "ks_radialBar_chart"){
                if (evt.target.dataItem){
                    var activePoint = evt.target.dataItem.dataContext;
                }
            }
            else{
                var activePoint = evt.target.dataItem.dataContext;
            }
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
                    self._rpc({
                        model: 'ks_dashboard_ninja.item',
                        method: 'ks_fetch_drill_down_data',
                        args: [item_id, domain, sequnce]
                    }).then(function(result) {
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        if (result.ks_chart_data) {
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                            if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                                self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                            } else {
                                self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                                self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                            }
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');

                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                            var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                            if (item_data.ks_dashboard_item_type === 'ks_flower_view'){
                                self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                self.ksrenderflowerchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                            }else if(item_data.ks_dashboard_item_type == 'ks_radialBar_chart'){
                                self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                self.ksrenderradialchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                            }else if(item_data.ks_dashboard_item_type == 'ks_bullet_chart'){
                                self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                self.ksrenderbulletchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                            }else if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                                self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                                self.ksrenderfunnelchart(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]"),item_data);
                            }else{
                                self._renderChart($(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]), item_data);
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

                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');

                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');
                            var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                            var $container = self.renderListViewData(item_data);
                            $(self.$el.find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container).addClass('ks_overflow');
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

                        self.do_action(action, {
                            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                        });
                    }
                }
            }
        },


})

});