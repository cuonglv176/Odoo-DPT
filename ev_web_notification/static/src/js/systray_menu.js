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
        let self = this;
        this.action = useService("action");
        this.orm = useService("orm");
        this.props._activities = this._getActivityData();
        this.activityCounter = 0;
        this.busService = this.env.services.bus_service;
        this.busService.addEventListener("notification", ({detail: notifications}) => {
            for (const {payload, type} of notifications) {
                if (type === "notification_updated") {
                    self._getActivityData();
                    self._onMessageNotificationUpdate(payload);
                }
            }
        });
        this.busService.start()
    }

    async openRecord(activity) {
        document.body.click();
        let self = this;
        await this.orm.call('mail.message', 'update_status_message', [activity.id]);
        self._updateActivityPreview();
        this.action.doAction(
            {
                type: 'ir.actions.act_window',
                res_model: activity.model,
                res_id: activity.res_id,
                views: [[false, 'form']],
                target: 'current',
            }
        );
        this._getActivityData();
    }

    async _onMessageNotificationUpdate(payload) {
        if (payload) {
            if (payload.notification_unseen) {
                this.activityCounter++;
            }
            if (payload.notification_seen && this.activityCounter > 0) {
                this.activityCounter--;
            }
            window.$('.o_notification_counter').text(this.activityCounter);
            let permission = await Notification.requestPermission();
            let self = this;
            if (permission && payload) {
                payload.forEach((i) => {
                    if (i.message.subject_notification) {
                        let subject_notification = i.message.subject_notification
                        const noti = new Notification(subject_notification, {
                            body: subject_notification,
                            icon: '/logo.png'
                        });
                        noti.addEventListener('click', function () {
                            self.action.doAction(
                                {
                                    type: 'ir.actions.act_window',
                                    res_model: i.model,
                                    res_id: i.res_id,
                                    views: [[false, 'form']],
                                    target: 'current',
                                }
                            );
                        });
                    }
                });
            }
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
        this.props._activities = result;
        window.$('.o_notification_counter').text(self.activityCounter);
        return result;
    }
}

SystrayMenu.template = "systray_Activity_Menu";
SystrayMenu.components = {
    Dropdown,
    DropdownItem,
};
export const systrayItem = {Component: SystrayMenu,};
registry.category("systray").add("SystrayMenu", systrayItem, {sequence: 1});