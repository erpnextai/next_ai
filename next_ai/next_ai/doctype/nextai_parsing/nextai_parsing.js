// Copyright (c) 2025, NextAI Team and contributors
// For license information, please see license.txt

frappe.ui.form.on('NextAI Parsing', {
    doc: function (frm) {
        if (!frm.doc.doc) return;

        // Clear existing child rows before adding new ones
        frm.clear_table('parsing_details');

        // Fetch metadata of the selected Doctype
        frappe.model.with_doctype(frm.doc.doc, function () {
            const meta = frappe.get_meta(frm.doc.doc);

            // Loop through fields
            meta.fields.forEach(field => {
                // Skip Section/Column/Tab breaks
                if (['Section Break', 'Column Break', 'Tab Break'].includes(field.fieldtype)) return;

                // Add child row
                let child = frm.add_child('parsing_details');
                child.field_name = field.fieldname;
                child.field_label = field.label;
                child.field_type = field.fieldtype;
            });

            frm.refresh_field('parsing_details');
            frappe.msgprint(__('Fields added from Doctype: {0}', [frm.doc.doctype]));
        });
    }
});
