frappe.listview_settings['NextAI Model Info'] = {
    onload: function(listview) {
        // Set default filter
        listview.filter_area.add([["NextAI Model Info", "is_active", "=", "1"]]);
    }
};
