frappe.listview_settings['Sales Invoice'] = {
    onload: function (listview) {
        listview.page.add_inner_button(__("Bulk Upload to Digitax"), function () {
            let selected_docs = listview.get_checked_items();
            if (selected_docs.length === 0) {
                frappe.msgprint(__("Please select at least one Sales Invoice"));
                return;
            }

            let invoice_names = selected_docs.map(doc => doc.name);

            frappe.confirm(
                __("Are you sure you want to upload {0} selected invoices to Digitax?", [selected_docs.length]),
                function () {
                    frappe.call({
                        method: "nra_integration.integration.sales_invoice_integration.bulk_sync_invoices_to_digitax",
                        args: {
                            invoice_names: invoice_names
                        },
                        freeze: true,
                        callback: function (r) {
                            if (r.message && r.message.status === "success") {
                                frappe.show_alert({
                                    message: r.message.message,
                                    indicator: "green"
                                });
                            } else if (r.message && r.message.status === "partial_success") {
                                frappe.msgprint({
                                    title: __("Bulk Sync Partial Success"),
                                    message: r.message.message,
                                    indicator: "orange"
                                });
                            } else {
                                frappe.msgprint({
                                    title: __("Bulk Sync Failed"),
                                    message: r.message ? r.message.message : __("Unknown error occurred"),
                                    indicator: "red"
                                });
                            }
                            listview.refresh();
                        }
                    });
                }
            );
        }, __("Digitax"));
    }
};
