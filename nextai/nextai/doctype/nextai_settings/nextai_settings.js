// Copyright (c) 2025, antonykumar15898@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('NextAI Settings', {
	is_subscription: function(frm) {
		if (frm.doc.is_subscription) {
			frm.doc.is_free = 0
		} else {
			frm.doc.is_free = 1
		}
		frm.refresh_field('is_free');
	},
	is_free: function(frm) {
		if (frm.doc.is_free) {
			frm.doc.is_subscription = 0;
		} else {
			frm.doc.is_subscription = 1;
		}
		frm.refresh_field('is_subscription');
	}
});
