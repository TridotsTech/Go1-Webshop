// Copyright (c) 2024, tridotstech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Erp Settings", {
	refresh(frm) {

	},
    import_all_pages(frm){
        frappe.call({
               method:'go1_webshop.go1_webshop.after_install.insert_pages',
               args:{
               },
               // freeze:true,
               callback: function(r) {
                      if(r && r.message == 'success'){
                             // frm.set_value("publisher",r.data)
                             // frm.refresh_field("publisher")
                      }else{
                             alert('Something Went Wrong')
                      }
               }
        })
 }
});
