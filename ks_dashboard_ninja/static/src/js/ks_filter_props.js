odoo.define('ks_dashboard_ninja.ks_dashboard_filter', function (require) {
"use strict";

var KsFilterProps = require('ks_dashboard_ninja.ks_dashboard');
var core = require('web.core');
var QWeb = core.qweb;
var datepicker = require("web.datepicker");
const { FIELD_OPERATORS, FIELD_TYPES } = require('web.searchUtils');
const field_utils = require('web.field_utils');


return KsFilterProps.include({

    events: _.extend({}, KsFilterProps.prototype.events, {
        'hide.bs.dropdown .ks_dn_selection_box > div': 'onKsDnFilterBoxContainerHide',
        'click .dn_filter_click_event_selector': 'onKsDnDynamicFilterSelect',
        'click .ks_custom_filter_add_condition': 'ksOnCustomFilterConditionAdd',
        'click .ks_custom_filter_section_delete': 'ksOnCustomFilterConditionRemove',
        'click .ks_dn_filter_apply': 'ksOnCustomFilterApply',
        'click .ks_dn_filter_remove_event': 'ksOnRemoveFilterFromSearchPanel',
        'change .ks_custom_filter_field_selector': 'ksOnCustomFilterFieldSelect',
        'change .ks_custom_filter_field_selector': 'ksOnCustomFilterFieldSelect',
        'change .ks_operator_option_selector': 'ksOnCustomFilterOperatorSelect',
        'change .ks_operator_option_selector': 'ksOnCustomFilterOperatorSelect',
    }),

    init: function(){
        this._super.apply(this, arguments);
        this.ksCustomFilterData = {
            OPERATORS : FIELD_OPERATORS,
            FIELD_TYPES : FIELD_TYPES,
            DECIMAL_POINT : 2,
        }
    },

    onKsDnFilterBoxContainerHide: function(ev){
        if(ev.clickEvent && ev.clickEvent.target && $(ev.clickEvent.target).parents(".ks_dn_filter_dropdown_container").length) {
            return false;
        }
    },

    onKsDnDynamicFilterSelect: function(ev){
        var self = this;
        if($(ev.currentTarget).hasClass('dn_dynamic_filter_selected')){
            self._ksRemoveDynamicFilter(ev.currentTarget.dataset['filterId']);
            $(ev.currentTarget).removeClass('dn_dynamic_filter_selected');
        } else {
            self._ksAppendDynamicFilter(ev.currentTarget.dataset['filterId']);
            $(ev.currentTarget).addClass('dn_dynamic_filter_selected');
        }
    },

    _ksAppendDynamicFilter: function(filterId){
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

    _ksRemoveDynamicFilter: function(filterId){
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

    _ksUpdateAddDomainIndexData : function(action, categ, params){
        // Update Domain Index: Add or Remove model related data, Update its domain, item ids
        // Fetch records for the effected items
        // Re-render Search box of this name if the value is add
        var self = this;
        var model = params['model'] || false;
        var model_name = params['model_name'] || '';
        $(".ks_dn_filter_applied_container").removeClass('ks_hide');

        var filters_to_update = _(this.ks_dashboard_data.ks_dashboard_pre_domain_filter).values().filter((x)=>{return x.active === true && x.categ === categ});
        var domain_data = self.ks_dashboard_data.ks_dashboard_domain_data[model];
        if (domain_data) {
            var domain_index = _(domain_data.ks_domain_index_data).find((x)=>{return x.categ === categ});
            if (domain_index) {
                domain_index['domain'] = [];
                domain_index['label'] = [];
                _(filters_to_update).each((x)=>{
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
                }
                _(filters_to_update).each((x)=>{
                    if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                    domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                    domain_index['label'] = domain_index['label'].concat(x['name']);
                })
                domain_data.ks_domain_index_data.push(domain_index);
            }

            var $filter_container = $(QWeb.render('ks_dn_filter_section_container_template', {
                                    ks_domain_data: domain_data,
                                    ks_model: model,
                                }));
            $('.ks_dn_filter_section_container[data-ks-model-selector="'+ model + '"]').replaceWith($filter_container);

        } else {
            var domain_index = {
                    categ: categ,
                    domain: [],
                    label: [],
                    model: model,
            }
            _(filters_to_update).each((x)=>{
                if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                domain_index['label'] = domain_index['label'].concat(x['name']);
            })
            domain_data = {
                'domain': [],
                'model_name': model_name,
                'item_ids': self.ks_dashboard_data.ks_model_item_relation[model],
                'ks_domain_index_data': [domain_index],
            }
            self.ks_dashboard_data.ks_dashboard_domain_data[model] = domain_data;
            var $filter_container = $(QWeb.render('ks_dn_filter_section_container_template', {
                                    ks_domain_data: domain_data,
                                    ks_model: model,
                                }));
            $('.ks_dn_filter_applied_container').prepend($filter_container);
        }

        domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);

        _(domain_data['item_ids']).each((x)=>{self.ksFetchUpdateItem(x)});
    },

    _ksUpdateRemoveDomainIndexData: function(action, categ, params){
        var self = this;
        var model = params['model'] || false;
        var model_name = params['model_name'] || '';
        var filters_to_update = _(this.ks_dashboard_data.ks_dashboard_pre_domain_filter).values().filter((x)=>{return x.active === true && x.categ === categ});
        var domain_data = self.ks_dashboard_data.ks_dashboard_domain_data[model];
        var domain_index = _(domain_data.ks_domain_index_data).find((x)=>{return x.categ === categ});

        if (filters_to_update.length<1) {
            if (domain_data.ks_domain_index_data.length>1){
                domain_data.ks_domain_index_data.splice(domain_data.ks_domain_index_data.indexOf(domain_index),1);
                $('.o_searchview_facet[data-ks-categ="'+ categ + '"]').remove();
            }else {
                $('.ks_dn_filter_section_container[data-ks-model-selector="'+ model + '"]').remove();
                delete self.ks_dashboard_data.ks_dashboard_domain_data[model];
                if(!_(self.ks_dashboard_data.ks_dashboard_domain_data).keys().length){
                    $(".ks_dn_filter_applied_container").addClass('ks_hide');
                }
            }
        } else{
            domain_index['domain'] = [];
            domain_index['label'] = [];
            _(filters_to_update).each((x)=>{
                if (domain_index['domain'].length>0) domain_index['domain'].unshift('|');
                domain_index['domain'] = domain_index['domain'].concat(x['domain']);
                domain_index['label'] = domain_index['label'].concat(x['name']);
            })
            var $filter_container = $(QWeb.render('ks_dn_filter_section_container_template', {
                                    ks_domain_data: domain_data,
                                    ks_model: model,
                                }));
            $('.ks_dn_filter_section_container[data-ks-model-selector="'+ model + '"]').replaceWith($filter_container);
        }

        domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);
        _(domain_data['item_ids']).each((x)=>{self.ksFetchUpdateItem(x)});
    },

    _ksMakeDomainFromDomainIndex: function(ks_domain_index_data){
        var domain = [];
        _(ks_domain_index_data).each((x)=>{
            if (domain.length>0) domain.unshift('&');
            domain = domain.concat((x['domain']));
        })
        return domain;
    },

    ksGetParamsForItemFetch: function(item_id) {
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

    ks_fetch_items_data: function(){
        var self = this;
        return this._super.apply(this, arguments).then(function(){
            if (self.ks_dashboard_data.ks_dashboard_domain_data) self.ks_init_domain_data_index();
        });
    },

    ks_init_domain_data_index: function(){
        var self = this;
        // TODO: Make domain data index from backend : loop wasted
        var temp_data = {};
        var to_insert = _(this.ks_dashboard_data.ks_dashboard_pre_domain_filter).values().filter((x)=>{
            return x.type==='filter' && x.active && self.ks_dashboard_data.ks_dashboard_domain_data[x.model].ks_domain_index_data.length === 0
        });
        _(to_insert).each((x)=>{
            if(x['categ'] in temp_data) {
               temp_data[x['categ']]['domain']= temp_data[x['categ']]['domain'].concat(x['domain']);
               temp_data[x['categ']]['label']= temp_data[x['categ']]['label'].concat(x['name']);
            } else {
                temp_data[x['categ']] = {'domain': x['domain'], 'label': [x['name']], 'categ': x['categ'], 'model': x['model']};
            }
        })
        _(temp_data).values().forEach((x)=>{
            self.ks_dashboard_data.ks_dashboard_domain_data[x.model].ks_domain_index_data.push(x);
        })
    },

    // Custom Filter Events and Functions -------------------------------------------------------------------

    ksRenderDashboard: function(){
        var self = this;
        this._super.apply(this, arguments);
        var show_remove_option = false;
        if (Object.values(self.ks_dashboard_data.ks_dashboard_custom_domain_filter).length>0) self.ks_render_custom_filter(show_remove_option);
    },

    ks_render_custom_filter: function(show_remove_option){
        var $container = $(QWeb.render('ks_dn_custom_filter_input_container', {
                                    ks_dashboard_custom_domain_filter: Object.values(this.ks_dashboard_data.ks_dashboard_custom_domain_filter),
                                    show_remove_option: show_remove_option,
                                }));

        var first_field_select = Object.values(this.ks_dashboard_data.ks_dashboard_custom_domain_filter)[0]
        var field_type = first_field_select.field_type;
        var operators = this.ksCustomFilterData.OPERATORS[this.ksCustomFilterData.FIELD_TYPES[field_type]];
        var operator_type = operators[0];
        var $operator_input = $(QWeb.render('ks_dn_custom_domain_input_operator', {
                                    operators: operators,
                                }));
        $container.append($operator_input);

        var $value_input = this._ksRenderCustomFilterInputSection(operator_type, this.ksCustomFilterData.FIELD_TYPES[field_type], first_field_select.special_data)
        if ($value_input) $container.append($value_input);

        $("#ks_dn_custom_filters_container").append($container);
    },

    _ksRenderCustomFilterInputSection: function(operator_type, field_type, special_data){
        var $value_input;
        switch (field_type) {
            case 'boolean':
                return false;
                break;
            case 'selection':
                if ('value' in operator_type) return false;
                else $value_input = $(QWeb.render('ks_dn_custom_domain_input_selection', {
                                    selection_input: special_data['select_options'] || [],
                                }));
                break;
            case 'date':
            case 'datetime':
                if ('value' in operator_type) return false;
                $value_input = this._ksRenderDateTimeFilterInput(operator_type, field_type);
                break;
            case 'char':
            case 'id':
            case 'number' :
                if ('value' in operator_type) return false;
                else $value_input = $(QWeb.render('ks_dn_custom_domain_input_text', {}));
                break;
            default:
                return;
        }
        return $value_input;
    },

    _ksRenderDateTimeFilterInput: function(operator, field_type){
        var $value_container = $(QWeb.render('ks_dn_custom_domain_input_date'));
        switch(field_type) {
            case 'date':
                var $date_time_picker = new(datepicker.DateWidget)(this);
                $date_time_picker.appendTo($value_container).then((function() {
                    $date_time_picker.$el.addClass("ks_dn_filter_first_date_time_widget o_input");
                    $date_time_picker.setValue(moment());
                }).bind(this));

                if (operator.symbol === 'between') {
                    var $date_time_picker_2 = new(datepicker.DateWidget)(this);
                    $date_time_picker_2.appendTo($value_container).then((function() {
                        $date_time_picker_2.$el.addClass("ks_dn_filter_second_date_time_widget o_input");
                        $date_time_picker_2.setValue(moment());
                    }).bind(this));
                }
                break;
            case 'datetime':
                var $date_time_picker = new(datepicker.DateTimeWidget)(this);
                $date_time_picker.appendTo($value_container).then((function() {
                    $date_time_picker.$el.addClass("ks_dn_filter_first_date_time_widget o_input");
                    $date_time_picker.setValue(moment('00:00:00', 'hh:mm:ss'));
                }).bind(this));

                if (operator.symbol === 'between') {
                    var $date_time_picker_2 = new(datepicker.DateTimeWidget)(this);
                    $date_time_picker_2.appendTo($value_container).then((function() {
                        $date_time_picker_2.$el.addClass("ks_dn_filter_second_date_time_widget o_input");
                        $date_time_picker_2.setValue(moment('23:59:59', 'hh:mm:ss'));
                    }).bind(this));
                }
                break;
        }

        return $value_container;
    },

    ksOnCustomFilterConditionAdd: function(){
        var show_remove_option = true;
        this.ks_render_custom_filter(show_remove_option);
    },

    ksOnCustomFilterConditionRemove: function(ev){
        ev.stopPropagation();
        $(ev.currentTarget.parentElement).remove();
    },

    ksOnCustomFilterFieldSelect: function(ev){
        var $parent_container = $(ev.currentTarget.parentElement);
        $parent_container.find('.ks_operator_option_selector').remove();
        $parent_container.find('.o_generator_menu_value').remove();

        var field_id = ev.currentTarget.value;
        var field_select = this.ks_dashboard_data.ks_dashboard_custom_domain_filter[field_id];
        var field_type = field_select.field_type;
        var operators = this.ksCustomFilterData.OPERATORS[this.ksCustomFilterData.FIELD_TYPES[field_type]];
        var operator_type = operators[0];
        var $operator_input = $(QWeb.render('ks_dn_custom_domain_input_operator', {
                                   operators: operators,
                               }));

        $parent_container.append($operator_input);
        var $value_input = this._ksRenderCustomFilterInputSection(operator_type, this.ksCustomFilterData.FIELD_TYPES[field_type], field_select.special_data)
        if ($value_input) $parent_container.append($value_input);
    },

    ksOnCustomFilterOperatorSelect: function(ev){
        var $parent_container = $(ev.currentTarget.parentElement);
        var operator_symbol = ev.currentTarget.value;
        var field_id = $parent_container.find('.ks_custom_filter_field_selector').val();
        var field_select = this.ks_dashboard_data.ks_dashboard_custom_domain_filter[field_id];
        var field_type = field_select.field_type;
        var operator_type = this.ksCustomFilterData.OPERATORS[this.ksCustomFilterData.FIELD_TYPES[field_type]][ev.currentTarget.selectedIndex];

        $parent_container.find('.o_generator_menu_value').remove();
        var $value_input = this._ksRenderCustomFilterInputSection(operator_type, this.ksCustomFilterData.FIELD_TYPES[field_type], field_select.special_data)
        if ($value_input) $parent_container.append($value_input);
    },

    ksOnCustomFilterApply: function(){
        var model_domain = {};
        $('.ks_dn_custom_filter_input_container_section').each((index, filter_container) => {
            var field_id = $(filter_container).find('.ks_custom_filter_field_selector').val();
            var field_select = this.ks_dashboard_data.ks_dashboard_custom_domain_filter[field_id];
            var field_type = field_select.field_type;
            var domainValue = [];
            var domainArray = [];
            var operator = this.ksCustomFilterData.OPERATORS[this.ksCustomFilterData.FIELD_TYPES[field_type]][$(filter_container).find('.ks_operator_option_selector').prop('selectedIndex')];
            var label = field_select.name + ' ' + operator.description;
            if ('value' in operator){
                domainValue = [operator.value];
            } else if (['date', 'datetime'].includes(field_type)) {
                var dateValue = [];
                $(filter_container).find(".o_generator_menu_value .o_datepicker").each((index, $input_val) => {
                    var a = $($input_val).find("input").val();;
                    var b = field_utils.parse[field_type](a, { field_type }, { timezone: true });
                    var c = field_utils.format[field_type](b, { field_type }, { timezone: true });
                    domainValue.push(b.toJSON());
                    dateValue.push(c);
                });
                label = label +' ' + dateValue.join(" and " );
            } else if (field_type === 'selection') {
                domainValue = [$(filter_container).find(".o_generator_menu_value").val()]
                label = label + ' ' + $(filter_container).find(".o_generator_menu_value").val();
            }
            else {
                domainValue = [$(filter_container).find(".o_generator_menu_value input").val()]
                label = label +' ' + $(filter_container).find(".o_generator_menu_value input").val();
            }

            if (operator.symbol === 'between') {
                domainArray.push(
                    [field_select.field_name, '>=', domainValue[0]],
                    [field_select.field_name, '<=', domainValue[1]]
                );
                domainArray.unshift('&');
            } else {
                domainArray.push([field_select.field_name, operator.symbol, domainValue[0]]);
            }

            if(field_select.model in model_domain){
                model_domain[field_select.model]['domain'] = model_domain[field_select.model]['domain'].concat(domainArray);
                model_domain[field_select.model]['domain'].unshift('|');
                model_domain[field_select.model]['label'] = model_domain[field_select.model]['label'] + ' or ' +  label;
            } else {
                model_domain[field_select.model] = {
                    'domain': domainArray,
                    'label': label,
                    'model_name': field_select.model_name,
                }
            }
        });
        this._ksAddCustomDomain(model_domain);
    },

    _ksAddCustomDomain: function(model_domain){
        var self = this;
        $(".ks_dn_filter_applied_container").removeClass('ks_hide');
        _(model_domain).each((val,model)=>{
            var domain_data = self.ks_dashboard_data.ks_dashboard_domain_data[model];
            var domain_index = {
                categ: false,
                domain: val['domain'],
                label: [val['label']],
                model: model,
            }

            if (domain_data) {
                domain_data.ks_domain_index_data.push(domain_index);
                var $filter_container = $(QWeb.render('ks_dn_filter_section_container_template', {
                                    ks_domain_data: domain_data,
                                    ks_model: model,
                                }));
                $('.ks_dn_filter_section_container[data-ks-model-selector="'+ model + '"]').replaceWith($filter_container);
            } else {
                domain_data = {
                    'domain': [],
                    'model_name': val.model_name,
                    'item_ids': self.ks_dashboard_data.ks_model_item_relation[model],
                    'ks_domain_index_data': [domain_index],
                }
                self.ks_dashboard_data.ks_dashboard_domain_data[model] = domain_data;
                var $filter_container = $(QWeb.render('ks_dn_filter_section_container_template', {
                                    ks_domain_data: domain_data,
                                    ks_model: model,
                                }));
                $('.ks_dn_filter_applied_container').prepend($filter_container);
            }

            $("#ks_dn_custom_filters_container").empty();
            var show_remove_option = false;
            self.ks_render_custom_filter(show_remove_option);

            domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);
            _(domain_data['item_ids']).each((x)=>{self.ksFetchUpdateItem(x)});
        })
    },

    ksOnRemoveFilterFromSearchPanel: function(ev){
        var self = this;
        ev.stopPropagation();
        var $search_section = $(ev.currentTarget).parent();
        var model = $search_section.data('ksModel');
        if ($search_section.data('ksCateg')){
            var categ = $search_section.data('ksCateg');
            var action = 'remove_dynamic_filter';
            var $selected_pre_define_filter = $(".dn_dynamic_filter_selected.dn_filter_click_event_selector[data-ks-categ='"+ categ +"']");
            $selected_pre_define_filter.removeClass("dn_dynamic_filter_selected");
            _($selected_pre_define_filter).each((x,y)=>{
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
                if(!_(self.ks_dashboard_data.ks_dashboard_domain_data).keys().length){
                    $(".ks_dn_filter_applied_container").addClass('ks_hide');
                }
            } else {
                $search_section.remove();
            }

            domain_data['domain'] = self._ksMakeDomainFromDomainIndex(domain_data.ks_domain_index_data);
            _(domain_data['item_ids']).each((x)=>{self.ksFetchUpdateItem(x)});
        }
    },

})

});