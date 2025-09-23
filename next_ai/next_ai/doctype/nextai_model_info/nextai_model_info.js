// Copyright (c) 2025, erpnextai@gmail.com and contributors
// For license information, please see license.txt
var isWarningMessage=true;
frappe.ui.form.on('NextAI Model Info', {
	refresh: function(frm) {
		if (isWarningMessage){
			frappe.warn(
				'⚠️ Are you sure you want to proceed?',
				`
				<div style="font-size:14px; line-height:1.5;">
					<b>Please change or manipulate data in this Doctype only if you are aware of it.</b><br><br>
					Our <b>NextAI Team</b> prepared this information based on the official developer documentation.<br><br>
					If you are not sure, please check with our support team here:<br>
					👉 <a href="https://www.erpnextai.in/support" target="_blank" style="color:#1a73e8; text-decoration:none;">
						NextAI Support
					</a>
				</div>
				`,
				() => {
					frm.set_df_property('platform', 'read_only', 0);
					frm.set_df_property('model_name', 'read_only', 0);
					frm.set_df_property('is_active', 'read_only', 0);
					frm.set_df_property('knowledge_cutoff', 'read_only', 0);
					frm.set_df_property('verbose', 'read_only', 0);
					frm.set_df_property('subscription_rpm', 'read_only', 0);
					frm.set_df_property('free_rpm', 'read_only', 0);
					frm.set_df_property('free_rpd', 'read_only', 0);
				},
				'Continue',
				true // Sets dialog as minimizable
			);
		}
		isWarningMessage=true;
	},
	after_save: function(frm) {
		isWarningMessage=false;
	}
});
