// Copyright (c) 2025, Antony Praveenkumar Moses and contributors
// For license information, please see license.txt

frappe.ui.form.on('NextAI Prompt', {
	refresh: function(frm) {
		setFieldLableOptions(frm);
	},
	ref_doctype: function(frm) {
		if (frm.doc.ref_doctype) {
			setFieldLableOptions(frm);
		}
	},
	field_lable: function(frm) {
		console.log(frm.doc.field_lable);
	}	
});


const setFieldLableOptions = (frm) => {
	frappe.call({
		method: "next_ai.next_ai.doctype.nextai_prompt.nextai_prompt.get_field_type_fielname",
		type: "POST",
		args: {ref_doctype: frm.doc.ref_doctype},
		async: false,
		callback: function(r) {
			console.log(r.message);
			if (r.message.length > 0) {
				const fieldLableOptions = r.message.map((item) => ({ value: item.label, label: item.label }));
				frm.fields_dict.field_lable.set_data(fieldLableOptions);
			} else {
				frappe.msgprint(__("No fields found for the selected doctype."));
			}
		}
	})
}