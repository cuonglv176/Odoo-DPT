/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import {KsDashboardNinja} from "@ks_dashboard_ninja/js/ks_dashboard_ninja_new";
import { _t } from "@web/core/l10n/translation";
import { renderToElement,renderToString } from "@web/core/utils/render";
import { isBrowserChrome, isMobileOS } from "@web/core/browser/feature_detection";
import { Ksdashboardtile } from '@ks_dashboard_ninja/components/ks_dashboard_tile_view/ks_dashboard_tile';

patch(KsDashboardNinja.prototype,{
    ks_fetch_items_data(){
        var self = this;
        return super.ks_fetch_items_data().then(function(){
            if (self.ks_dashboard_data.ks_dashboard_domain_data) self.ks_init_domain_data_index();
        });
    },

    ks_init_domain_data_index(){
        var self = this;
        // TODO: Make domain data index from backend : loop wasted
        var temp_data = {};
        var to_insert = Object.values(this.ks_dashboard_data.ks_dashboard_pre_domain_filter).filter((x)=>{
            return x.type==='filter' && x.active && self.ks_dashboard_data.ks_dashboard_domain_data[x.model].ks_domain_index_data.length === 0
        });
        (to_insert).forEach((x)=>{
            if(x['categ'] in temp_data) {
               temp_data[x['categ']]['domain']= temp_data[x['categ']]['domain'].concat(x['domain']);
               temp_data[x['categ']]['label']= temp_data[x['categ']]['label'].concat(x['name']);
            } else {
                temp_data[x['categ']] = {'domain': x['domain'], 'label': [x['name']], 'categ': x['categ'], 'model': x['model']};
            }
        })
        Object.values(temp_data).forEach((x)=>{
            self.ks_dashboard_data.ks_dashboard_domain_data[x.model].ks_domain_index_data.push(x);
        })
    },
        onKsDnDynamicFilterSelect(ev){
        var self = this;
        if($(ev.currentTarget).hasClass('dn_dynamic_filter_selected')){
            self._ksRemoveDynamicFilter(ev.currentTarget.dataset['filterId']);
            $(ev.currentTarget).removeClass('dn_dynamic_filter_selected');
        } else {
            self._ksAppendDynamicFilter(ev.currentTarget.dataset['filterId']);
            $(ev.currentTarget).addClass('dn_dynamic_filter_selected');
        }
    },

    _ksAppendDynamicFilter(filterId){
        // Update predomain data -> Add into Domain Index -> Add or remove class
        this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].active = true;

        var action = 'add_dynamic_filter';
        var categ = this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].categ;
        var params = {
            'model': this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].model,
            'model_name': this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].model_name,
        }
        this._ksUpdateAddDomainIndexData(action, categ, params);
    },

    _ksRemoveDynamicFilter(filterId){
         // Update predomain data -> Remove from Domain Index -> Add or remove class
        this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].active = false;

        var action = 'remove_dynamic_filter';
        var categ = this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].categ;
        var params = {
            'model': this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].model,
            'model_name': this.ks_dashboard_data.ks_dashboard_pre_domain_filter[filterId].model_name,
        }
        this._ksUpdateRemoveDomainIndexData(action, categ, params);
    },

    _ksUpdateAddDomainIndexData(action, categ, params){
        // Update Domain Index: Add or Remove model related data, Update its domain, item ids
        // Fetch records for the effected items
        // Re-render Search box of this name if the value is add
        var self = this;
        var model = params['model'] || false;
        var model_name = params['model_name'] || '';
        $(".ks_dn_filter_applied_container").removeClass('ks_hide');

        var filters_to_update = Object.values(this.ks_dashboard_data.ks_dashboard_pre_domain_filter).filter((x)=>{return x.active === true && x.categ === categ});
        var domain_data = self.ks_dashboard_data.ks_dashboard_domain_data[model];
        if (domain_data) {
            var domain_index = (domain_data.ks_domain_index_data).find((x)=>{return x.categ === categ});
            if (domain_index) {
                domain_index['domain'] = [];
                domain_index['label'] = [];
                (filters_to_update).forEach((x)=>{
                    if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                    domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                    domain_index['label'] = domain_index['label'].concat(x['name']);
                })
            } else {
                domain_index = {
                    categ: categ,
                    domain: [],
                    label: [],
                    model: model,
                };
                filters_to_update.forEach((x)=>{
                    if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                    domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                    domain_index['label'] = domain_index['label'].concat(x['name']);
                });
                domain_data.ks_domain_index_data.push(domain_index);
            }

        } else {
            var domain_index = {
                    categ: categ,
                    domain: [],
                    label: [],
                    model: model,
            };
            filters_to_update.forEach((x)=>{
                if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                domain_index['label'] = domain_index['label'].concat(x['name']);
            });
            domain_data = {
                'domain': [],
                'model_name': model_name,
                'item_ids': self.ks_dashboard_data.ks_model_item_relation[model],
                'ks_domain_index_data': [domain_index],
            };
            self.ks_dashboard_data.ks_dashboard_domain_data[model] = domain_data;
        }

        domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);
        self.state.pre_defined_filter = {...domain_data}
        self.state.ksDateFilterSelection = 'none'
    },

    _ksUpdateRemoveDomainIndexData(action, categ, params){
        var self = this;
        var model = params['model'] || false;
        var model_name = params['model_name'] || '';
        var filters_to_update = Object.values(this.ks_dashboard_data.ks_dashboard_pre_domain_filter).filter((x)=>{return x.active === true && x.categ === categ});
        var domain_data = self.ks_dashboard_data.ks_dashboard_domain_data[model];
        var domain_index = (domain_data.ks_domain_index_data).find((x)=>{return x.categ === categ});

        if (filters_to_update.length<1) {
            if (domain_data.ks_domain_index_data.length>1){
                domain_data.ks_domain_index_data.splice(domain_data.ks_domain_index_data.indexOf(domain_index),1);
                $('.o_searchview_facet[data-ks-categ="'+ categ + '"]').remove();
            }else {
                $('.ks_dn_filter_section_container[data-ks-model-selector="'+ model + '"]').remove();
                delete self.ks_dashboard_data.ks_dashboard_domain_data[model];
                if(!Object.keys(self.ks_dashboard_data.ks_dashboard_domain_data).length){
                    $(".ks_dn_filter_applied_container").addClass('ks_hide');
                }
            }
        } else{
            domain_index['domain'] = [];
            domain_index['label'] = [];
            (filters_to_update).forEach((x)=>{
                if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                domain_index['label'] = domain_index['label'].concat(x['name']);
            })
        }

        domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);
        domain_data['ks_remove'] = true
         self.state.pre_defined_filter = {...domain_data}
         self.state.ksDateFilterSelection = 'none'
    },

    _ksMakeDomainFromDomainIndex(ks_domain_index_data){
        var domain = [];
        (ks_domain_index_data).forEach((x)=>{
            if (domain.length>0) domain.unshift('&');
            domain = domain.concat((x['domain']));
        })
        return domain;
    },
    ksOnRemoveFilterFromSearchPanel(ev){
        var self = this;
        ev.stopPropagation();
        var $search_section = $(ev.currentTarget).parent();
        var model = $search_section.data('ksModel');
        if ($search_section.data('ksCateg')){
            var categ = $search_section.data('ksCateg');
            var action = 'remove_dynamic_filter';
            var $selected_pre_define_filter = $(".dn_dynamic_filter_selected.dn_filter_click_event_selector[data-ks-categ='"+ categ +"']");
            $selected_pre_define_filter.removeClass("dn_dynamic_filter_selected");
            ($selected_pre_define_filter).toArray().forEach((x)=>{
                var filter_id = $(x).data('filterId');
                self.ks_dashboard_data.ks_dashboard_pre_domain_filter[filter_id].active = false;
            })
            var params = {
                'model': model,
                'model_name': $search_section.data('ksModelName'),
            }
            this._ksUpdateRemoveDomainIndexData(action, categ, params);
        } else {
            var index = $search_section.index();
            var domain_data = self.ks_dashboard_data.ks_dashboard_domain_data[model];
            domain_data.ks_domain_index_data.splice(index, 1);

            if (domain_data.ks_domain_index_data.length === 0) {
                $('.ks_dn_filter_section_container[data-ks-model-selector="'+ model + '"]').remove();
                delete self.ks_dashboard_data.ks_dashboard_domain_data[model];
                if(!Object.keys(self.ks_dashboard_data.ks_dashboard_domain_data).length){
                    $(".ks_dn_filter_applied_container").addClass('ks_hide');
                }
            } else {
                $search_section.remove();
            }

            domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);
            domain_data['ks_remove'] = true
            self.state.pre_defined_filter = {...domain_data}
            self.state.ksDateFilterSelection = 'none'
        }
    },

    ksGetParamsForItemFetch(item_id) {
        var self = this;
        var model1 = self.ks_dashboard_data.ks_item_model_relation[item_id][0];
        var model2 = self.ks_dashboard_data.ks_item_model_relation[item_id][1];

        if(model1 in self.ks_dashboard_data.ks_model_item_relation) {
            if (self.ks_dashboard_data.ks_model_item_relation[model1].indexOf(item_id)<0)
                self.ks_dashboard_data.ks_model_item_relation[model1].push(item_id);
        }else {
            self.ks_dashboard_data.ks_model_item_relation[model1] = [item_id];
        }

        if(model2 in self.ks_dashboard_data.ks_model_item_relation) {
            if (self.ks_dashboard_data.ks_model_item_relation[model2].indexOf(item_id)<0)
                self.ks_dashboard_data.ks_model_item_relation[model2].push(item_id);
        }else {
            self.ks_dashboard_data.ks_model_item_relation[model2] = [item_id];
        }

        var ks_domain_1 = self.ks_dashboard_data.ks_dashboard_domain_data[model1] && self.ks_dashboard_data.ks_dashboard_domain_data[model1]['domain'] || [];
        var ks_domain_2 = self.ks_dashboard_data.ks_dashboard_domain_data[model2] && self.ks_dashboard_data.ks_dashboard_domain_data[model2]['domain'] || [];

        return {
            ks_domain_1: ks_domain_1,
            ks_domain_2: ks_domain_2,
        }
    },

});