frappe.ui.form.on("Sales Invoice", {
    refresh: function (frm) {

        // 🟢 Synced
        if (frm.doc.digitax_invoice_id) {
            frm.dashboard.set_headline_alert(
                `<div class="indicator green">${__("Invoice is synced with Digitax")}</div>`
            );

            // 🔥 ADD THIS BLOCK (Fetch QR Button)
            if (!frm.doc.nra_qr_code) {
                frm.add_custom_button(__("Fetch QR Details"), function () {
                    frappe.call({
                        method: "nra_integration.customizations.sales_invoice_qr.fetch_digitax_invoice_details",
                        args: {
                            invoice_name: frm.doc.name
                        },
                        freeze: true,
                        callback: function (r) {
                            if (r.message && r.message.status === "success") {
                                frappe.show_alert({
                                    message: __("QR Code fetched successfully"),
                                    indicator: "green"
                                });
                                frm.reload_doc();
                            } else {
                                frappe.msgprint({
                                    title: __("Fetch Failed"),
                                    message: r.message ? r.message.message : __("Unable to fetch QR"),
                                    indicator: "red"
                                });
                            }
                        }
                    });
                }, __("Digitax"));
            }

            // 🆕 Generate QR Button
            if (frm.doc.nra_qr_code && !frm.doc.digitax_qr) {
                frm.add_custom_button(__("Generate QR"), function () {
                    frappe.call({
                        method: "nra_integration.integration.sales_invoice_integration.generate_digitax_qr",
                        args: {
                            invoice_name: frm.doc.name
                        },
                        freeze: true,
                        callback: function (r) {
                            if (r.message && r.message.status === "success") {
                                frappe.show_alert({
                                    message: __("QR Image generated successfully"),
                                    indicator: "green"
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __("Digitax"));
            }

            // 🔴 Failed
        } else if (frm.doc.digitax_sync_status === "Failed") {
            frm.dashboard.set_headline_alert(
                `<div class="indicator red">${__("Digitax Sync Failed")}</div>`
            );

            // 🟠 Pending
        } else if (frm.doc.docstatus === 1) {
            frm.dashboard.set_headline_alert(
                `<div class="indicator orange">${__("Pending Sync with Digitax")}</div>`
            );
        }

        // 🔵 Link Button (only if not synced)
        if (!frm.doc.digitax_invoice_id) {
            frm.add_custom_button(__("Link with Digitax"), function () {
                frappe.call({
                    method: "nra_integration.integration.sales_invoice_integration.manual_sync_invoice_to_digitax",
                    args: {
                        invoice_name: frm.doc.name
                    },
                    freeze: true,
                    callback: function (r) {
                        if (r.message && r.message.status === "success") {
                            frappe.show_alert({
                                message: __("Invoice linked to Digitax successfully! ID: {0}", [r.message.digitax_id]),
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
            }, __("Create"));
        }
    }
});