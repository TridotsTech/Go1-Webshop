frappe.ui.form.on("Go1 Webshop Settings", {
	refresh(frm) {
	},
       import_all_pages(frm){
            // console.log("CLicked");
            fetchThemesAndShowDialog(frm);
            frm.reload_doc()
       }
   });
//    function fetchThemesAndShowDialog(frm) {
//         frappe.call({
//             method: 'go1_webshop.go1_webshop.after_install.fetch_themes_from_external_url',
//             callback: function(r) {
//                 console.log("CCC",r.message)
//                 if (r.message) {
//                     showThemeDialog(frm, r.message);
//                 } else {
//                     frappe.msgprint('No theme found.');
//                 }
//             }    
//         });
      
//    }
   function fetchThemesAndShowDialog(frm) {
        frappe.call({
            method: 'go1_webshop.go1_webshop.after_install.fetch_erp_ecommerce_themes_from_external_url',
            callback: function(r) {
                // console.log("CCC",r.message)
                if (r.message) {
                    showThemeDialog(frm, r.message);
                } else {
                    frappe.msgprint('No theme found.');
                }
            }    
        });
      
   }

   
   function showThemeDialog(frm, themes) {
       let selectedThemeRoute = null;
       
       const dialog = new frappe.ui.Dialog({
           title: 'Select a Theme',
           fields: [{
               label: 'Choose Theme',
               fieldname: 'theme',
               fieldtype: 'HTML',
               options: generateThemeOptionsHtml(themes)
            }],
            size:"extra-large",
            primary_action_label: 'Import Pages',
            primary_action: function() {
                dialog.hide();
                // console.log("selectedThemeRoute", selectedThemeRoute);
                if (selectedThemeRoute) {
                    importPages(frm, selectedThemeRoute);

                } else {
                    frappe.msgprint('Please select a theme.');
                }
            }
       });
   
       dialog.show();
       window.selectTheme = function(themeName, themeRoute) {
        // console.log("themeName", themeName);

        selectedThemeRoute = themeRoute;
           $('.theme-container').removeClass('selected');
           $(`div[data-theme-name="${themeName}"]`).addClass('selected');
       };
   }
   
   function generateThemeOptionsHtml(themes) {
       let style = `
       <style>
              .modal.show .modal-dialog{
                display: flex;
                justify-content: center;
              }
              .modal-content{
              }

              .text_div h4{
                font-weight: 500;
                transition: .2s;
                color: #525252;
              }
           .theme-container {
                padding: 10px;
                width: 350px;
                height: 333px;
                text-align: center;
                cursor: pointer;
                position: relative;
                border-radius: 5px;
                border: 1px solid #ededed;
                transition: border-color 0.3s;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                align-items: center;
           }
           .theme-container.selected {
            .text_div h4{
                font-weight: 600;
                transition: .2s;
                font-size: 16px !important;
                text-shadow: 6px 5px 5px #bebebe5e;
                color: #525252;
            }
                .theme-img {
                    width: 100%;
                    height: 96%;
                    transition: 0.2s;
                }
                border-color: #4CAF50;
                box-shadow: 0 0 7px -4px;
           }
           .theme-container:hover {
                box-shadow: 0 0 7px -4px;
            }
           .theme-container.selected::after {
               content: '✔';
               color: #fff;
               font-size: 24px;
               position: absolute;
               top: -11px;
               right: -11px;
               background: #4CAF50;
               width: 30px;
               height: 30px;
               border-radius: 50%;
               display: flex;
               align-items: center;
               justify-content: center;
           }
           .img_div{
                height: 80%;
           }
           .theme-img {
               width: 100%;
               height: 100%;
               transition: 0.2s;
           }
           .theme-container:hover {
            img.theme-img{
                width: 100%;
                height: 96%;
                }
            .text_div h4{
                font-weight: 600;
                text-shadow: 6px 5px 5px #bebebe5e;
                color: #525252;
                font-size: 16px !important;
                transition: .2s;
            }
            }
            .contains{
                height: 100%;
            }
       </style>
   `;
   
       let html = '<div style="display: flex; flex-wrap: wrap; justify-content: flex-start; gap: 20px;">' + style;
       themes.forEach(theme => {
           html += `
               <div class="theme-container" onclick="selectTheme('${theme.theme_name}', '${theme.theme_route}')" data-theme-name="${theme.theme_name}">
                    <div class="contains">
                        <div class="img_div"><img src="${theme.theme_image}" class="theme-img"></div>
                        <div class="text_div"><h4 style="font-size: 15px;" class="mt-3">${theme.theme_name}</h4></div>
                    </div>
               </div>
           `;
       });
       html += '</div>';
       return html;
   }

   

   function importPages(frm, theme) {
    // console.log("Themes", theme);
    frm.set_value('selected_theme', theme);
    // console.log(theme);

    frappe.call({
        method: 'go1_webshop.go1_webshop.after_install.insert_pages',
        args: { theme: theme },
        callback: function(r) {
            // console.log("r",r)
            if (r.message === 'success') {
                frappe.msgprint('Pages imported successfully');
                frm.save();
            } else {
                frappe.msgprint('Something went wrong during page import');
            }
        },
        freeze:true,
        freeze_message:"Please wait, this may take few minutes."
    });

    // Initial progress at 0%
    // frappe.show_progress(__('Importing Pages'), 25, 100, 'Starting import...');

    // frappe.realtime.on('import_progress', function(data) {
    //     let progress = 0;
    //     if (data.stage === 'items') {
    //         console.log("60%");
    //         progress = 60;
    //     }

    //     frappe.show_progress(__('Importing Pages'), progress, 100, data.message);

    //     if (progress >= 100) {
    //         frappe.hide_progress();
    //     }
    // });
}