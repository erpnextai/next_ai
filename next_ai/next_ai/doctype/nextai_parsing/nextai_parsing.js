frappe.ui.form.on('NextAI Parsing', {
    doc: function (frm) {
        if (!frm.doc.doc) return;

        frm.clear_table('parsing_details');

        // Fetch parser-type details first
        frappe.call({
            method: "next_ai.ai.utils.get_parser_type_details",
            callback: function(r) {
                const parser_map = r.message || {};

                // Fetch metadata of selected Doctype
                frappe.model.with_doctype(frm.doc.doc, function () {
                    const meta = frappe.get_meta(frm.doc.doc);

                    meta.fields.forEach(field => {
                        // skip breaks
                        if (['Section Break', 'Column Break', 'Tab Break'].includes(field.fieldtype)) 
                            return;

                        // get parser rules for this field.type
                        const rule = parser_map[field.fieldtype];

                        // skip if rule not found OR inactive
                        if (!rule || !rule.is_active) return;

                        // Add child row
                        let child = frm.add_child('parsing_details');
                        child.field_name = field.fieldname;
                        child.field_label = field.label;
                        child.field_type = field.fieldtype;
                        child.description = rule.default_description;
                    });

                    frm.refresh_field('parsing_details');
                    frappe.msgprint(__('Active fields added from Doctype: {0}', [frm.doc.doc]));
                });
            }
        });
    }
});
