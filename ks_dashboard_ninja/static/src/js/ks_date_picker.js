odoo.define("ks_dashboard_ninja.ks_date_picker", function(require) {
    "use strict";
    var datepicker = require("web.datepicker");

    datepicker.DateWidget.include({

        _onDateTimePickerShow: function() {
            this._super.apply(this, arguments);

            if (this.name === "ks_dashboard") {
                window.removeEventListener('scroll', this._onScroll, true);
            }
        },
    });
    return datepicker;
})