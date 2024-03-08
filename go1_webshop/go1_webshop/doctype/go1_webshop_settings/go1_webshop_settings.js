// Copyright (c) 2024, tridotstech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Go1 Webshop Settings", {
	refresh(frm) {
	},
       import_all_pages(frm){
        console.log('import_all_pages',$("#loader"))
        
        if( $("#loader").length != 0){
              console.log('sssss');
              $("#loader").css("display", "block");
        }else{
              console.log('aaaaaa  ');
              let loader = document.createElement('p')
              loader.id = 'loader'
              loader.textContent = 'Loading...'
              document.querySelector('[data-fieldtype=Button]').parentNode.append(loader)
        }
             $('[data-fieldtype=Button]').hide()  
              frappe.call({
                     method:'go1_webshop.go1_webshop.after_install.insert_pages',
                     args:{
                     },
                     // freeze:true,
                     callback: function(r) {
                            $('[data-fieldtype=Button]').show()                           
                            $('#loader').hide()
                            frappe.msgprint(__('Pages imported successfully'));
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

