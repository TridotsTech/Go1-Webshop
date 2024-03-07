import frappe
import json
import os
import zipfile
from frappe.utils import encode, get_files_path
def after_install():
	unzip_builder_images()
	insert_custom_fields()
	insert_component()
	
def insert_component():
	file_name = "builder_components.json"
	insert_component_data(file_name)

@frappe.whitelist()
def insert_pages():
	insert_builder_settings()
	insert_slider_images()
	insert_all_script_data()
	insert_all_pages()
	insert_item_groups()
	insert_item()
	insert_website_item()
	insert_mobile_menu()
	return 'success'

def insert_item():
	file_name = "item.json"
	insert_item_data(file_name)

def insert_mobile_menu():
	file_name = "mobile_menu.json"
	insert_mobile_menu_data(file_name)
 
def insert_website_item():
	file_name = "website_item.json"
	insert_item_data(file_name)
	 
def insert_all_script_data():
	file_name = "builder_scripts.json"
	read_script_module_path(file_name)
	
def insert_all_pages():
	file_name = "builder_pages.json"
	read_page_module_path(file_name)
	webshop_settings = frappe.get_single("Webshop Settings")
	webshop_settings.products_per_page = 20
	webshop_settings.enable_variants=1
	webshop_settings.show_stock_availability=1
	webshop_settings.show_price=1
	webshop_settings.enabled=1
	company = frappe.db.get_all("Company")
	webshop_settings.company=company[0].name
	webshop_settings.enable_wishlist=1
	webshop_settings.price_list="Standard Selling"
	webshop_settings.quotation_series="SAL-QTN-.YYYY.-"
	webshop_settings.default_customer_group="All Customer Groups"
	webshop_settings.save(ignore_permissions=True)


def insert_builder_settings():
	file_name = "builder_settings.json"
	read_builder_settings_module_path(file_name)

def insert_slider_images():
	file_name = "website_slider.json"
	read_module_path(file_name)

def insert_item_groups():
	file_name = "item_groups.json"
	insert_item_groups_data(file_name)

def insert_custom_fields():
	file_name = "custom_fields.json"
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				# frappe.log_error(frappe.db.exists({"doctype": i.get('doctype'), "item_name": i.get('item_name')}))
				if(not frappe.db.exists({"doctype": i.get('doctype'), "name": i.get('name')})):
					frappe.get_doc(i).insert()
			except frappe.NameError:
				pass
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), file_name)

def read_module_path(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				if(not frappe.db.exists({"doctype": "Website Slideshow", "name": "Landing Page"})):
					frappe.get_doc(i).insert()
			except frappe.NameError:
				pass
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), file_name)

def insert_mobile_menu_data(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				if(not frappe.db.exists({"doctype": "Mobile Menu", "label": i.get("label")})):
					frappe.get_doc(i).insert()
			except frappe.NameError:
				pass
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), file_name)
    
def insert_component_data(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				# if(not frappe.db.exists({"doctype": "Component", "name": i.get('component_id')})):
				frappe.get_doc(i).insert()
			except frappe.NameError:
				pass
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), file_name)
	
def insert_item_data(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		item_codes = []
		warehouse = None
		for i in out:
			try:
				# frappe.log_error(frappe.db.exists({"doctype": i.get('doctype'), "item_name": i.get('item_name')}))
				if(not frappe.db.exists({"doctype": i.get('doctype'), "item_name": i.get('item_name')})):
					if i.get('doctype')=="Website Item":
						company = frappe.db.get_all("Company",fields=['abbr'])
						if company:
							i["website_warehouse"] = "Stores - "+company[0].abbr
							warehouse = "Stores - "+company[0].abbr
					frappe.get_doc(i).insert()
					if i.get('doctype')=="Website Item":
						price_doc = frappe.new_doc("Item Price")
						price_doc.item_code=i.get("item_code")
						price_doc.price_list="Standard Selling"
						price_doc.selling=1
						price_doc.price_list_rate=5000
						price_doc.save(ignore_permissions=True)
						item_codes.append(i.get("item_code"))
			except frappe.NameError:
				pass
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), file_name)
		if file_name == "website_item.json":
			if item_codes and warehouse:
				stock_entry = frappe.new_doc("Stock Entry")
				stock_entry.stock_entry_type = "Material Receipt"
				for x in item_codes:
					stock_entry.append("items",{
						"t_warehouse":warehouse,
						"item_code":x,
						"qty":10
						})
				stock_entry.docstatus=1
				stock_entry.save(ignore_permissions=True)

def insert_item_groups_data(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				if(not frappe.db.exists({"doctype": i.get('doctype'), "name": i.get('__name')})):
					script_doc = frappe.get_doc(i).insert()
					
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "read_script_module_path")
		frappe.db.set_value("Item Group","Products","show_in_website",0)
	frappe.db.commit()
def unzip_builder_images():
	"""Unzip current file and replace it by its children"""
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,"go1_webshop_files.zip")
	with zipfile.ZipFile(file_path) as z:
		frappe.log_error("file_list",z.filelist)
		for file in z.filelist:
			if file.is_dir() or file.filename.startswith("__MACOSX/"):
				# skip directories and macos hidden directory
				continue
			filename = os.path.basename(file.filename)
			if filename.startswith("."):
				# skip hidden files
				continue
			origin = get_files_path()
			item_file_path = os.path.join(origin, file.filename.split("/")[1])
			if not os.path.exists(item_file_path):
				file_doc = frappe.new_doc("File")
				file_doc.content = z.read(file.filename)
				file_doc.file_name = filename
				file_doc.folder = "Home"
				file_doc.is_private = 0
				file_doc.save()

def read_page_module_path(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
			out_json = {}
		for index,i in enumerate(out):
			try:
				if i.get('client_scripts') :
					out_json[i.get('page_title')] = i['client_scripts']
					del i['client_scripts']					
				if(not frappe.db.exists({"doctype": i.get('doctype'), "page_title": i.get('page_title')})):
					page_doc = frappe.get_doc(i).insert()
					frappe.db.set_value(i.get('doctype'), page_doc.get('name'), 'route', i.get('route'))
					# frappe.log_error(title="out_json[index]", message=out_json)
					if(out_json[i.get('page_title')]):
						for child_index,script in enumerate(out_json[i.get('page_title')]):
							# frappe.log_error(title="queryyyy", message=f"""INSERT INTO `tabBuilder Page Client Script` (name,builder_script,parent,parentfield,parenttype)
							# VALUES ('{script.get('builder_script')}','{script.get('builder_script')}','{page_doc.name}','client_scripts','Builder Page') """)
							frappe.db.sql(f"""INSERT INTO `tabBuilder Page Client Script` (name,builder_script,parent,parentfield,parenttype)
							VALUES ('{script.get('builder_script') + str(index) + str(child_index)}','{script.get('builder_script')}','{page_doc.name}','client_scripts','Builder Page') """)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "read_page_module_path")
		frappe.db.set_value("Website Settings","Website Settings","home_page","f-landing")
def read_script_module_path(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				if(not frappe.db.exists({"doctype": i.get('doctype'), "name": i.get('__name')})):
					script_doc = frappe.get_doc(i).insert()
					frappe.db.sql("""UPDATE `tabBuilder Client Script` SET 
								name=%(c_name)s WHERE name=%(s_name)s""",{"c_name":i.get('__name'),"s_name":script_doc.name})
					frappe.db.commit()
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "read_script_module_path")
	frappe.db.commit()
	
def read_builder_settings_module_path(file_name):
	path = frappe.get_module_path("go1_webshop")
	file_path = os.path.join(path,'json_data',file_name)
	if os.path.exists(file_path):
		out = ''
		with open(file_path, 'r') as f:
			out = json.load(f)
		try:
			frappe.get_doc(out).insert()
		except frappe.NameError:
			pass
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), file_name)