// Copyright (c) 2025, NextAI Team and contributors
// For license information, please see license.txt
var fieldlabelOptions;

frappe.ui.form.on('NextAI Prompt', {
	refresh: function(frm) {
		
		frm.page.set_secondary_action(__('Video'), function() {
			window.open('https://www.erpnextai.in/video#h.xnfsg3y7wo22', '_blank');
		});
		frm.page.btn_secondary.addClass('btn-primary');
        
		frm.fields_dict['generate_prompt_template'].$input.addClass('btn-primary');

		if (frappe.user_roles.includes('System Manager')){
			frm.set_df_property('is_user_specific', 'read_only', 0)
		}

		if (! frm.doc.user){
			frm.set_value('user', frappe.session.user)
		}

		if (frm.doc.ref_doctype){
			setFieldlabelOptions(frm)
		}

		frm.set_query("user", function() {
            return {
                query: "next_ai.next_ai.doctype.nextai_prompt.nextai_prompt.filter_user_field",
            };
        });
	},
	ref_doctype: function(frm) {
		if (frm.doc.ref_doctype) {
			setFieldlabelOptions(frm);
			frm.set_value('field_name', null);
			frm.set_value('field_type', null);
			frm.set_value('field_label', null);
		}
	},
	field_label: function(frm) {
		for (let data of fieldlabelOptions){
			if (data['label'] == frm.doc.field_label){
				frm.set_value('field_name', data['fieldname'])
				frm.set_value('field_type', data['fieldtype'])
				frm.set_value('prompt', null)
			}
		}
	},
	is_user_specific: function(frm){
		if (frm.doc.is_user_specific === 0){
			frappe.confirm("⚠️ Please note: If you uncheck this field, it will affect the <b> prompt for the entire organization</b>. 🏢<br>👉 Kindly make sure you are fully aware of the impact before making any changes. ✨",
				() => {
					// action to perform if Yes is selected
					frm.set_df_property('user', 'reqd', 0)
					frm.set_df_property('user', 'hidden', 1)
				}, () => {
					// action to perform if No is selected
					frm.doc.is_user_specific = 1
					frm.refresh_field('is_user_specific')
				})
		}else{
			frappe.msgprint("This will work only for the selected user")
			frm.set_df_property('user', 'reqd', 1)
			frm.set_df_property('user', 'hidden', 0)
		}
	},
	generate_prompt_template: function(frm){
		if (!frm.doc.field_type){
			frappe.throw('Please select the Doctype and Fieldlabel for prompt generation')
		}
		frappe.call({
			method: "next_ai.next_ai.doctype.nextai_prompt.nextai_prompt.generate_prompt",
			args: {field_type: frm.doc.field_type},
			async: false,
			callback: function(r) {
				if (r.message.length > 0) {
					frm.set_value('prompt', r.message)
				}
			}
		})
	},
	enable: function(frm){
		if (frm.doc.enable == 1 && frm.doc.ref_doctype && frm.doc.field_label){
			frappe.call({
				method: "next_ai.next_ai.doctype.nextai_prompt.nextai_prompt.validate_enable_check",
				args: {
					ref_doctype: frm.doc.ref_doctype,
					field_name: frm.doc.field_name,
					user: frm.doc.user ? frm.doc.user : "",
					is_user_specific: frm.doc.is_user_specific
				},
				callback: function(r){
					if (!r.message){
						frm.set_value("enable", 0);
                    	frm.refresh_field("enable");
					}
				}
			})
		}
	}
});


const setFieldlabelOptions = (frm) => {
	frappe.call({
		method: "next_ai.next_ai.doctype.nextai_prompt.nextai_prompt.get_field_type_fielname",
		type: "POST",
		args: {ref_doctype: frm.doc.ref_doctype},
		async: false,
		callback: function(r) {
			if (r.message.length > 0) {
				fieldlabelOptions = r.message
				const labelOptions = r.message.map((item) => ({ value: item.label, label: item.label }));
				frm.fields_dict.field_label.set_data(labelOptions);
			} else {
				frappe.msgprint(__("No fields found for the selected doctype."));
				frm.set_value("field_label", null)
				const labelOptions = []
				frm.fields_dict.field_label.set_data(labelOptions);
			}
		}
	})
}