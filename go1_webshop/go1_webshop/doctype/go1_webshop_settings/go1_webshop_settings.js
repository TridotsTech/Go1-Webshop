// Copyright (c) 2024, tridotstech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Go1 Webshop Settings", {
	refresh(frm) {
	},
       import_all_pages(frm){
        console.log('import_all_pages')
             
              frappe.call({
                     method:'go1_webshop.go1_webshop.after_install.insert_pages',
                     args:{
                     },
                     // freeze:true,
                     callback: function(r) {
                            if(r && r.message == 'success'){
                                   // console.log('llll');
                                   frappe.msgprint(__('Pages imported successfully'));
                            }else{
                                   alert('Something Went Wrong')
                            }
                     }
              })
       }
});

