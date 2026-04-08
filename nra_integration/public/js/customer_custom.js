frappe.ui.form.on("Customer", {
    refresh: function (frm) {
        // Status Indicators
        if (frm.doc.digitax_customer_id) {
            frm.dashboard.set_headline_alert(
                `<div class="indicator green">${__("Customer is synced with Digitax")}</div>`
            );
        } else if (frm.doc.digitax_sync_status === "Failed") {
            frm.dashboard.set_headline_alert(
                `<div class="indicator red">${__("Digitax Sync Failed")}</div>`
            );
        } else {
            frm.dashboard.set_headline_alert(
                `<div class="indicator orange">${__("Pending Sync with Digitax")}</div>`
            );
        }

        // Button 1: Integrate Customer with Digitax (POST)
        if (!frm.is_new() && !frm.doc.digitax_customer_id) {
            frm.add_custom_button(__("Integrate Customer with Digitax"), function () {
                frappe.call({
                    method: "nra_integration.integration.customer_integration.integrate_customer_to_digitax",
                    args: {
                        customer_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Integrating customer with Digitax..."),
                    callback: function (r) {
                        if (r.message && r.message.status === "success") {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: "green"
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __("Integration Failed"),
                                message: r.message ? r.message.message : __("Unknown error occurred."),
                                indicator: "red"
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }, __("Actions"));
        }

        // Button 2: Get Customer Digitax ID (GET) - hidden once ID is fetched
        if (!frm.is_new() && !frm.doc.digitax_customer_id) {
            frm.add_custom_button(__("Get Customer Digitax ID"), function () {
                frappe.call({
                    method: "nra_integration.integration.customer_integration.get_customer_digitax_id",
                    args: {
                        customer_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Fetching Digitax ID..."),
                    callback: function (r) {
                        if (r.message && r.message.status === "success") {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: "green"
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __("Fetch Failed"),
                                message: r.message ? r.message.message : __("Unknown error occurred."),
                                indicator: "red"
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }, __("Actions"));
        }
    }
});
