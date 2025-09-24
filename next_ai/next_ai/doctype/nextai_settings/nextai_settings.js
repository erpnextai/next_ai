// Copyright (c) 2025, erpnextai@gmail.com and contributors
// For license information, please see license.txt
var usage_log_retention_days
frappe.ui.form.on('NextAI Settings', {
	refresh: function(frm){
		frm.set_query("model_name", function() {
        return {
            filters: {
                "is_active": 1,
                "platform": frm.doc.platform
            }
        };
    });
	},
	onload: function(frm) {
		usage_log_retention_days = frm.doc.usage_log_retention_days
	},
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
	},
	usage_log_retention_days: function(frm) {
		frappe.confirm('⚠️ Increasing this value will retain more Usage Logs, which may consume more database space. Please increase only if you know what you are doing.',
			() => {
				// action to perform if Yes is selected

			}, () => {
				// action to perform if No is selected
				frm.doc.usage_log_retention_days = usage_log_retention_days
				frm.refresh_field('usage_log_retention_days');
		})



	}
});
