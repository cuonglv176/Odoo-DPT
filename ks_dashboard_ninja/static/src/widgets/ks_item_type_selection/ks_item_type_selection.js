/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component,useState} = owl;

export class KsDashboarditemtype extends Component {
        setup(){
           var self = this.props;
           this.state = useState({ charts: [
           {'id':0,'name':'Tile','Tech_name':'ks_tile'},
           {'id':1,'name':'Bar','Tech_name':'ks_bar_chart'},
           {'id':2,'name':'Horizontal Bar','Tech_name':'ks_horizontalBar_chart'},
           {'id':3,'name':'Line','Tech_name':'ks_line_chart'},
           {'id':4,'name':'Area','Tech_name':'ks_area_chart'},
           {'id':5,'name':'Pie','Tech_name':'ks_pie_chart'},
           {'id':6,'name':'Doughnut','Tech_name':'ks_doughnut_chart'},
           {'id':7,'name':'Polar','Tech_name':'ks_polarArea_chart'},
           {'id':8,'name':'Radial','Tech_name':'ks_radialBar_chart'},
           {'id':9,'name':'Scatter','Tech_name':'ks_scatter_chart'},
           {'id':10,'name':'Radar','Tech_name':'ks_radar_view'},
           {'id':11,'name':'Flower','Tech_name':'ks_flower_view'},
           {'id':12,'name':'Funnel','Tech_name':'ks_funnel_chart'},
           {'id':13,'name':'Bullet','Tech_name':'ks_bullet_chart'},
           {'id':14,'name':'List','Tech_name':'ks_list_view'},
           {'id':15,'name':'Map','Tech_name':'ks_map_view'},
           {'id':16,'name':'To-do','Tech_name':'ks_to_do'},
           {'id':17,'name':'KPI','Tech_name':'ks_kpi'}
           ]});

        }

        onselectitemtype(ev){
          var ks_active_target =  $(ev.currentTarget.parentElement).find(".active")
          $.each(ks_active_target, function(index,item) {
            $(item).removeClass("active")
         });
         $(ev.currentTarget).addClass("active")
         var ks_value = (ev.currentTarget).innerText
         var ks_target =  this.state.charts.find((item)=>{
            return item.name === ks_value
         })
        this.props.record.update({ [this.props.name]: ks_target['Tech_name']})
        }

    }
KsDashboarditemtype.template="ks_dashboard_item_view_owl";
export const KsDashboarditemtypeField = {
    component:  KsDashboarditemtype,
    supportedTypes: ["char"],
};
registry.category("fields").add('ks_dashboard_item_type', KsDashboarditemtypeField);