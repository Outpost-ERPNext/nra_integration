frappe.ui.form.on("Item", {
    setup: function (frm) {
        frm.set_query("hsn_code", function () {
            return {
                query: "nra_integration.features.item_hsn_search.hsn_search"
            };
        });
    },
    refresh: function (frm) {
        // Status Indicators
        if (frm.doc.digitax_item_id) {
            frm.dashboard.set_headline_alert(
                `<div class="indicator green">${__("Item is synced with Digitax")}</div>`
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

        if (!frm.is_new() && !frm.doc.digitax_item_id) {
            frm.add_custom_button(__("Sync to Digitax"), function () {
                frappe.call({
                    method: "nra_integration.integration.item_integration.manual_sync_item_to_digitax",
                    args: {
                        item_code: frm.doc.item_code
                    },
                    freeze: true,
                    callback: function (r) {
                        if (r.message && r.message.status === "success") {
                            frappe.show_alert({
                                message: __("Item synced to Digitax successfully! ID: {0}", [r.message.digitax_id]),
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
