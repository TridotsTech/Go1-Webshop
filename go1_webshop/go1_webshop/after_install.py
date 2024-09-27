import frappe
import json
import os
import time
from frappe.utils import encode, get_files_path
import requests
from frappe import _
from frappe.utils.background_jobs import enqueue
from go1_webshop.go1_webshop.doctype.override_doctype.builder_page import log_css_template



# Don't Remove this API
# @frappe.whitelist(allow_guest=True)
# def fetch_themes_from_external_url():
#     external_url = "http://192.168.0.157:8225/api/method/go1_webshop_theme.go1_webshop_theme.utils.get_theme_list"
#     api_key = "4d689e50dcec946"
#     api_secret = "aaf1bc1c3c7e24a"

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"token {api_key}:{api_secret}"
#     }
#     try:
#         response = requests.post(external_url,headers=headers)
#         response.raise_for_status()
#         themes = response.json()
#         for theme in themes.get('message'):
#             theme['theme_image'] = domain_name + theme['theme_image']
#         return themes.get('message', [])
#     except requests.exceptions.RequestException as e:
#         frappe.throw(_('Error fetching themes from external URL: {0}').format(str(e)))


@frappe.whitelist(allow_guest=True)
def fetch_erp_ecommerce_themes_from_external_url():
    webshop_theme_settings = frappe.get_single("Go1 Webshop Theme Settings")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {webshop_theme_settings.api_key}:{webshop_theme_settings.api_secret}"
    }
    external_url = f"{webshop_theme_settings.url}/api/method/go1_webshop_theme.go1_webshop_theme.utils.fetch_erp_ecommerce_themes"

    try:
        response = requests.post(external_url,headers=headers)
        response.raise_for_status()
        themes = response.json()
        for theme in themes.get('message'):
            theme['theme_image'] = webshop_theme_settings.url + theme['theme_image']
        return themes.get('message', [])
    except requests.exceptions.RequestException as e:
        frappe.throw(_('Error fetching themes from external URL: {0}').format(str(e)))


@frappe.whitelist(allow_guest=True)
def handle_specific_endpoint(values):
    frappe.msgprint(f"Received data: {values}")
    return values


@frappe.whitelist(allow_guest=True)
def after_install():
    insert_custom_fields()
    # insert_component()
    get_theme()


@frappe.whitelist(allow_guest=True)
def get_theme():
    themes = [
                {"theme_name": "Go1 Furniture Theme", "doctype":"Go1 Webshop Theme", "theme_image": "/files/furniture.png", "theme_route": "Furniture Theme"},
                {"theme_name": "Go1 Fashion Theme", "doctype":"Go1 Webshop Theme", "theme_image": "/files/fashion.png", "theme_route": "Fashion Theme"}
            ]
    for theme in themes:
        exists = frappe.db.exists("Go1 Webshop Theme", {"theme_name": theme["theme_name"]})
        if not exists:
            doc = frappe.new_doc("Go1 Webshop Theme")
            doc.theme_name = theme["theme_name"]
            doc.theme_image = theme["theme_image"]
            doc.theme_route = theme["theme_route"]
            doc.insert()
            frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def insert_pages(theme):
    frappe.db.sql('''DELETE I
                    FROM `tabWishlist Item` I
                    INNER JOIN `tabWebsite Item` P ON P.name = I.website_item
                    WHERE P.is_go1_webshop_item = 1
                    ''')
    frappe.db.sql('''DELETE Q
                    FROM `tabQuotation` Q
                    INNER JOIN `tabQuotation Item` QI ON QI.parent = Q.name
                    INNER JOIN `tabItem` I ON QI.item_code = I.name
                    WHERE I.is_go1_webshop_item = 1
                ''')
    frappe.db.sql('DELETE FROM `tabItem` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabWebsite Item` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabItem Group` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabMobile Menu`')
    frappe.db.sql('DELETE FROM `tabItem Price` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabWebsite Slideshow Item` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabWebsite Slideshow` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabBuilder Page` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabBuilder Component` WHERE is_go1_webshop_item = 1')
    # frappe.db.sql('DELETE FROM `tabFile` WHERE is_go1_webshop_item = 1')
    frappe.db.sql('DELETE FROM `tabBuilder Client Script` WHERE is_go1_webshop_item = 1')

    def update_home_page(new_home_route):
        current_home_page = frappe.db.get_value('Website Settings', 'Website Settings', 'home_page')
        frappe.db.set_value('Website Settings', 'Website Settings', 'home_page', new_home_route)
        frappe.db.commit()

        home_route = "go1-landing"
        update_home_page(home_route)

    insert_custom_fields(theme)
    clear_cache_for_current_site()
    return 'success'


# @frappe.whitelist(allow_guest=True)
def clear_cache_for_current_site():
    current_site = frappe.local.site
    commands = f"bench --site {current_site} clear-cache"
    os.system(commands)
    # frappe.log_error("Current Site", commands)
    return commands




@frappe.whitelist(allow_guest=True)
def prepend_domain_to_image_urls(data, domain):
    """Recursively prepend domain to image URLs in the given dictionary or list."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("/files/"):
                data[key] = domain + value
                log_message = f"Updated URL for key {key}: {data[key]}"
                # frappe.log_error(log_message, "URL Update")
            elif isinstance(value, (dict, list)):
                prepend_domain_to_image_urls(value, domain)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                prepend_domain_to_image_urls(item, domain)


def update_blocks_with_domain(blocks, domain):
    """Update the blocks key with domain prepended to all src attributes."""
    try:
        blocks_data = json.loads(blocks)
        prepend_domain_to_image_urls(blocks_data, domain)
        return json.dumps(blocks_data)
    except json.JSONDecodeError as e:
        frappe.log_error(frappe.get_traceback(), "JSON Decode Error in update_blocks_with_domain")
        return blocks


MAX_LOG_LENGTH = 140
MAX_METHOD_LENGTH = 255


@frappe.whitelist()
def truncate_message(message):
    """Truncate message to fit the maximum allowed length."""
    # return message if len(message) <= MAX_LOG_LENGTH else message[:MAX_LOG_LENGTH] + '...'
    return message


def log_error_message(message, title):
    """Log error message in parts if it exceeds the max length."""
    # if len(message) > MAX_LOG_LENGTH:
    #     parts = [message[i:i+MAX_LOG_LENGTH] for i in range(0, len(message), MAX_LOG_LENGTH)]
    #     for index, part in enumerate(parts):
    #         frappe.log_error(part, f"{title} (part {index + 1})")
    # else:
    #     frappe.log_error(message, title)
    frappe.log_error(message, title)


def get_uploaded_file_content(filedata):
    try:
        import base64
        if filedata:
            if "," in filedata:
                filedata = filedata.rsplit(",", 1)[1]
            uploaded_content = base64.b64decode(filedata)
            return uploaded_content
        else:
            frappe.msgprint(_('No file attached'))
            return None
    except Exception as e:
        frappe.log_error("Error in seapi.get_uploaded_file_content", frappe.get_traceback())


@frappe.whitelist(allow_guest=True)
def insert_custom_fields(theme):
    import requests
    import os
    import shutil
    import zipfile
    from urllib.request import urlopen
    
    webshop_theme_settings = frappe.get_single("Go1 Webshop Theme Settings")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {webshop_theme_settings.api_key}:{webshop_theme_settings.api_secret}"
    }
    
    external_url = f"{webshop_theme_settings.url}/api/method/go1_webshop_theme.go1_webshop_theme.utils.get_all_json"


    try:
        response = requests.get(external_url, headers=headers, json={"theme": theme})
        response.raise_for_status()
        themes = response.json()

        message = themes.get("message", [])
        for row in message:
            for i, j in row.items():
                if i == "file_list":
                    from urllib.request import urlopen
                    import zipfile
                    source_path = frappe.get_module_path("go1_webshop")
                    file_path = os.path.join(source_path, "go1_webshop_files.zip")
                    if not os.path.exists(os.path.join(source_path, "go1_webshop_files.zip")):
                        try:
                            os.makedirs(os.path.join(source_path, theme))
                        except Exception as e:
                            frappe.log_error(f"Error while creating folder: {e}", frappe.get_traceback())
                            continue

                    try:
                        # frappe.log_error("File Path 157", j)
                        with urlopen(j) as data, open(file_path, 'wb') as zip_ref:
                            shutil.copyfileobj(data, zip_ref)
                        with zipfile.ZipFile(file_path, 'r') as file_data:
                            for file in file_data.infolist():
                                if file.is_dir() or file.filename.startswith("__MACOSX/"):
                                    continue
                                filename = os.path.basename(file.filename)
                                if filename.startswith("."):
                                    continue
                                origin = get_files_path()
                                item_file_path = os.path.join(origin, file.filename)
                                if not os.path.exists(item_file_path) and not frappe.db.exists("File", {"file_name": filename}):
                                    file_doc = frappe.new_doc("File")
                                    file_doc.content = file_data.read(file.filename)
                                    file_doc.file_name = filename
                                    file_doc.folder = "Home"
                                    file_doc.is_private = 0
                                    file_doc.save(ignore_permissions=True)
                    except Exception as e:
                        frappe.log_error(f"Error while downloading and extracting file", frappe.get_traceback())
                        continue

                # if i == "theme_css_files":
                #     try:
                #         if j:
                #             source_path = frappe.get_module_path("go1_webshop")
                #             theme_folder = os.path.join(source_path, "themes",theme)
                            
                #             if not os.path.exists(theme_folder):
                #                 os.makedirs(theme_folder)
                #             theme_css_path = os.path.join(source_path, "themes", theme, "theme.css")
                #             if os.path.exists(theme_folder):
                #                 with open(theme_css_path, 'w') as css_data:
                #                     css_data.write(j)
                #     except:
                #         frappe.log_error(f"Error while creating Theme CSS File{theme}", frappe.get_traceback())

                # if i == "root_css_files":
                #     try:
                #         if j:
                #             app_path = frappe.get_app_path("go1_webshop")
                #             theme_css_path = os.path.join(app_path, "public", "root.css")
                #             with open(theme_css_path, 'w') as css_data:
                #                 css_data.write(j)
                #     except:
                #         frappe.log_error(f"Error while creating Root CSS File{theme}", frappe.get_traceback())

                try:
                    if isinstance(j, dict):
                        if j['doctype'] == "Go1 Webshop Theme" and not frappe.db.exists({"doctype": j['doctype'], "name": j['name']}):
                            frappe.get_doc(j).insert(ignore_permissions=True)
                        if j['doctype'] == "Builder Settings" and not frappe.db.exists({"doctype": j['doctype'], "name": j['name']}):
                            frappe.get_doc(j).insert(ignore_permissions=True)

                    if isinstance(j, list):
                        for k in j:
                            if k['doctype'] == "Builder Component":
                                # frappe.enqueue(create_builder_component, queue='short', timeout=60, is_async=True, param=k, domain=webshop_theme_settings.url)
                                create_builder_component(k)
                            elif k['doctype'] == "Builder Client Script" and not frappe.db.exists({"doctype": k.get('doctype'), "name": k.get('name')}):
                                script_doc = frappe.get_doc(k).insert(ignore_permissions=True)
                                frappe.db.sql("""UPDATE `tabBuilder Client Script` SET name=%(c_name)s WHERE name=%(s_name)s""", {"c_name": k.get('name'), "s_name": script_doc.name})
                                frappe.db.commit()
                            elif k['doctype'] == "Custom Field" and not frappe.db.exists({"doctype": k['doctype'], "name": k['name']}):
                                frappe.get_doc(k).insert(ignore_permissions=True)
                            elif k['doctype'] == "Item Group" and not frappe.db.exists({"doctype": k['doctype'], "name": k['item_group_name']}):
                                frappe.get_doc(k).insert(ignore_permissions=True)
                            elif k['doctype'] == "Mobile Menu" and not frappe.db.exists({"doctype": k['doctype'], "name": k['name']}):
                                frappe.get_doc(k).insert(ignore_permissions=True)
                            elif k['doctype'] == "Website Slideshow" and not frappe.db.exists({"doctype": k['doctype'], "name": k['slideshow_name']}):
                                frappe.get_doc(k).insert(ignore_permissions=True)
                            elif k['doctype'] == "Item" and not frappe.db.exists({"doctype": k['doctype'], "name": k['name']}):
                                insert_item_data(j)
                                # frappe.get_doc(k).insert(ignore_permissions=True)
                            elif k['doctype'] == "Website Item" and not frappe.db.exists({"doctype": k['doctype'], "name": k['name']}):
                                insert_item_data(j)

                            elif k['doctype'] == "Builder Page":
                                read_page_module_path(j)
                            #     frappe.get_doc(k).insert(ignore_permissions=True)
                            
            
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), "insert_custom_fields_error")
                

    except Exception as e:
        frappe.throw(_('An unexpected error occurred: {0}').format(str(e)))


def create_builder_component(param):
    try:
        if not frappe.db.exists({"doctype": param['doctype'], "name": param['component_name']}):
            frappe.get_doc(param).insert(ignore_permissions=True)
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_builder_component_error")


def enqueue_with_retry(function, params, max_retries=5, retry_delay=10):
    attempt = 0
    while attempt < max_retries:
        try:
            job_name = truncate_data(f"{function.__name__}_{params.get('component_name', '')}", MAX_METHOD_LENGTH)
            frappe.enqueue(function, queue='default', param=params, job_name=job_name)
            return
        except frappe.exceptions.LockError:
            attempt += 1
            time.sleep(retry_delay)
    log_error_message(f"Failed to enqueue job after {max_retries} attempts", "enqueue_with_retry_error")


def truncate_data(data, max_length):
    """Truncate data to fit the maximum allowed length."""
    return data if len(data) <= max_length else data[:max_length]



def read_page_module_path(out):
        out_json = {}
        for index, i in enumerate(out):
            try:
                if i.get('client_scripts'):
                    out_json[i.get('page_title')] = i['client_scripts']
                    del i['client_scripts']
                if not frappe.db.exists({"doctype": i.get('doctype'), "page_title": i.get('page_title')}):
                    page_doc = frappe.get_doc(i).insert(ignore_permissions=True)

                    frappe.db.set_value(i.get('doctype'), page_doc.name, 'route', i.get('route'))
                    
                    if i.get('page_title') in out_json:
                        for child_index, script in enumerate(out_json[i.get('page_title')]):
                            script_name = f"{script.get('builder_script')}{page_doc.name}{child_index}"

                            frappe.db.sql(f"""INSERT INTO `tabBuilder Page Client Script` (name, builder_script, parent, parentfield, parenttype)
                            VALUES (%s, %s, %s, 'client_scripts', 'Builder Page')""",
                                        (script_name, script.get('builder_script'), page_doc.name))

                            frappe.db.commit()

            except Exception as e:
                frappe.log_error("read_page_module_path",frappe.get_traceback())
        for page in out:
            # if page.get('page_title') == "Furniture Landing":
            #     frappe.db.set_value("Website Settings", "Website Settings", "home_page", page.get('route'))
            #     break 
            # if page.get('page_title') == "Fashion Landing":
            #     frappe.db.set_value("Website Settings", "Website Settings", "home_page", page.get('route'))
            #     break
            if page.get('page_title') == "Go1 Landing":
                frappe.db.set_value("Website Settings", "Website Settings", "home_page", page.get('route'))


@frappe.whitelist(allow_guest=True)
def insert_item_data(out):
    item_codes = []
    warehouse = None
    max_log_length = 140
    
    for i in out:
        try:
            if not frappe.db.exists({"doctype": i.get('doctype'), "item_name": i.get('item_name')}):
                if i.get('doctype') == "Website Item":
                    company = frappe.db.get_all("Company", fields=['abbr'])
                    if company:
                        i["website_warehouse"] = "Stores - " + company[0].abbr
                        # i["website_image"] = domain_name + i["website_image"]
                        # frappe.log_error("i['website_image']",i["website_image"])
                        warehouse = "Stores - " + company[0].abbr

                if "india_compliance" in frappe.get_installed_apps() and i.get('doctype') == "Item":
                    i["gst_hsn_code"] = "999900"
        
                frappe.get_doc(i).insert(ignore_permissions=True)
            
                if i.get('doctype') == "Website Item":
                    price_doc = frappe.new_doc("Item Price")
                    price_doc.item_code = i.get("item_code")
                    price_doc.price_list = "Standard Selling"
                    price_doc.selling = 1
                    price_doc.price_list_rate = 5000
                    price_doc.is_go1_webshop_item = 1

                    # Check if the item exists before saving the price
                    if frappe.db.exists("Item", price_doc.item_code):
                        price_doc.save(ignore_permissions=True)
                        item_codes.append(i.get("item_code"))
                    else:
                        frappe.log_error(f"Item {price_doc.item_code} not found. Skipping price insertion.")

        except frappe.NameError:
            pass
        except Exception as e:
            error_message = frappe.get_traceback()
            # if len(error_message) > max_log_length:
            #     error_message = error_message[:max_log_length] + '...'
            frappe.log_error(error_message, "insert_item_data_error")