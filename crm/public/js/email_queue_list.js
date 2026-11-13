frappe.provide("frappe.listview_settings");

(function () {
	const prev_refresh = frappe.listview_settings["Email Queue"]?.refresh;

	frappe.listview_settings["Email Queue"] = Object.assign(
		frappe.listview_settings["Email Queue"] || {},
		{
			refresh: function (listview) {
				if (prev_refresh) {
					prev_refresh(listview);
				}
				add_bulk_send_selected_action(listview);
			},
		}
	);

	function add_bulk_send_selected_action(listview) {
		if (listview._bulk_send_action_added) return;
		listview._bulk_send_action_added = true;

		const send_selected = () => {
			if (listview._bulk_send_in_progress) {
				frappe.show_alert({
					message: __("Bulk send already in progress. Please wait..."),
					indicator: "orange",
				});
				return;
			}

			// Safely extract ONLY record name strings from selection
			const raw_items = (listview.get_checked_items ? listview.get_checked_items() : []) || [];
			const selected_names = raw_items
				.map((item) => {
					if (typeof item === "string") return item.trim();
					if (item && typeof item === "object" && item.name) return String(item.name).trim();
					return "";
				})
				.filter(Boolean);

			// Deduplicate record names
			const unique_names = Array.from(new Set(selected_names));

			if (!unique_names || unique_names.length === 0) {
				frappe.msgprint(__("Please select at least one Email Queue record using the checkboxes."));
				return;
			}

			frappe.confirm(
				__("Are you sure you want to send {0} selected email(s) immediately from the queue?", [
					unique_names.length,
				]),
				() => {
					listview._bulk_send_in_progress = true;
					frappe.show_progress(__("Sending Emails"), 0, unique_names.length, __("Initiating send..."));

					frappe.call({
						method: "crm.api.daily_allocation.bulk_send_email_queue",
						args: {
							names: unique_names,
							force_send: false,
						},
						freeze: true,
						freeze_message: __("Sending {0} selected email(s)...", [unique_names.length]),
						callback: (r) => {
							listview._bulk_send_in_progress = false;
							frappe.hide_progress();
							if (r && r.message) {
								const res = r.message;
								let msg = __(
									"Processed {0} email(s):<br>• <b>{1}</b> successfully sent<br>• <b>{2}</b> skipped<br>• <b>{3}</b> failed",
									[res.total_selected, res.sent, res.skipped, res.failed]
								);
								if (res.skipped > 0 && res.details?.skipped?.length) {
									const skipReasons = res.details.skipped
										.map((s) => `${s.name}: ${s.reason}`)
										.slice(0, 5)
										.join("<br>");
									msg += `<br><br><small class="text-muted">${skipReasons}</small>`;
								}
								frappe.msgprint({
									title: __("Bulk Email Queue Send Complete"),
									indicator: res.failed > 0 ? "orange" : "green",
									message: msg,
								});
							}
							listview.clear_checked_items();
							listview.refresh();
						},
						error: () => {
							listview._bulk_send_in_progress = false;
							frappe.hide_progress();
							frappe.msgprint({
								title: __("Bulk Send Failed"),
								indicator: "red",
								message: __("An error occurred while processing the queued emails."),
							});
						},
					});
				}
			);
		};

		listview.page.add_actions_menu_item(
			__("Send Selected"),
			send_selected,
			false,
			null,
			"send"
		);
	}
})();
