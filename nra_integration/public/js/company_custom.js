frappe.ui.form.on("Company", {
    refresh: function (frm) {
        // Status Indicators
        if (frm.doc.digitax_company_id) {
            frm.dashboard.set_headline_alert(
                `<div class="indicator green">${__("Company is synced with Digitax")}</div>`
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

        if (!frm.is_new() && !frm.doc.digitax_company_id) {
            frm.add_custom_button(__("Sync to Digitax"), function () {
                frappe.call({
                    method: "nra_integration.integration.company_integration.manual_sync_company_to_digitax",
                    args: {
                        company_name: frm.doc.name
                    },
                    freeze: true,
                    callback: function (r) {
                        if (r.message && r.message.status === "success") {
                            frappe.show_alert({
                                message: __("Company synced to Digitax successfully! ID: {0}", [r.message.digitax_id]),
                                indicator: "green"
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: __("Sync Failed"),
                                message: r.message ? r.message.message : __("Unknown error occurred during sync."),
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
