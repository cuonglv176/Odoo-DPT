/** @odoo-module **/
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Component, useRef, onPatched, onMounted, useState} from "@odoo/owl";
import {session} from "@web/session";
import {jsonrpc} from "@web/core/network/rpc_service";
import {renderToString} from "@web/core/utils/render";
import {Dropdown, DropdownItem} from "@web/core/dropdown/dropdown";
import {busService} from "@bus/services/bus_service";

class SystrayMenu extends Component {

    setup() {
        super.setup(...arguments);
        this.action = useService("action");
        this._activities = [];
        this.activityCounter = 0;
        this.busService = this.env.services.bus_service;
        this.channel = "mail_message_" + session.user_id
        this.busService.addChannel(this.channel)
        this.busService.addEventListener("notification", this._onMessageNotificationUpdate.bind(this))
        onMounted(this._getActivityData);
    }

    _onMessageNotificationUpdate(payload) {
        if (payload) {
            if (payload.notification_unseen) {
                this.activityCounter++;
            }
            if (payload.notification_seen && this.activityCounter > 0) {
                this.activityCounter--;
            }
            window.$('.o_notification_counter').text(this.activityCounter);
        }
    }

    isEmpty(records) {
        return !records.length;
    }

    async beforeOpen() {
        await this._getActivityData()
    }

    async onMarkAsRead(event) {
        let self = this;
        await jsonrpc('/web/dataset/call_kw', {
            model: 'mail.message',
            method: 'message_read_all',
            args: [[]],
            kwargs: {},
        })
        self._updateActivityPreview();
    }


    async _updateActivityPreview() {
        var self = this;
        await self._getActivityData()
    }

    async _getActivityData() {
        let self = this;
        if (!session.user_id) {
            self._activities = [];
            self.activityCounter = 0;
            window.$('.o_notification_counter').text(self.activityCounter);
            window.$el.toggleClass('o_no_notification', !self.activityCounter);
            return Promise.resolve([]);
        }
        let result = await jsonrpc('/web/dataset/call_kw', {
            model: 'res.users',
            method: 'ev_systray_get_activities',
            args: [],
            kwargs: {context: session.user_context},
        })
        self.activityCounter = result.reduce((total_count, p_data) => total_count + p_data.total_count || 0, 0);
        let $content = window.$('.o_mail_systray_dropdown_items').append(
                $(renderToString('systray_Activity_Menu_Previews', {
                    activities: self._activities,
                    isEmpty: self.isEmpty
                }))
            )
        ;
        // this.$target.find('.o_mail_systray_dropdown_items')
        console.log(result)
    }
}

SystrayMenu.template = "systray_Activity_Menu";
SystrayMenu.components = {
    Dropdown,
    DropdownItem,
};
export const systrayItem = {Component: SystrayMenu,};
registry.category("systray").add("SystrayMenu", systrayItem, {sequence: 1});