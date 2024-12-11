from frappe import _
import frappe
import json
import requests
from frappe import _
from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from frappe.utils import cint
from go1_webshop.go1_webshop.query import ProductQuery
from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website

def currency(amount):
	return "rs"+amount 

@frappe.whitelist()
def logout_customer():
	frappe.local.cookie_manager.delete_cookie('sid')
	frappe.local.cookie_manager.delete_cookie('user_id')
	return {"status":"Success"}

def update_website_context(context):
	# context.favicon = "/assets/go1_builder/go1_builder/gf-favicon.png"
	return ""
	
@frappe.whitelist()
def insert_new_address(doc):
	if frappe.db.exists("Address",doc["name"]):
		address = frappe.get_doc("Address",doc["name"]).update(doc)
		address.save(ignore_permissions = True)
		frappe.db.commit()
		return address
	else:
		address = frappe.new_doc("Address").update(doc)
		address.insert(ignore_permissions = True)
		return address
	

@frappe.whitelist()
def get_address_data(doc):
	return frappe.get_doc("Address",doc)

@frappe.whitelist()
def delete_address_data(doc):
	try:
		address = frappe.get_doc("Address",doc)
		address.delete(ignore_permissions = True)
		return "Successfully Deleted"
	except frappe.exceptions.LinkExistsError:
		if frappe.db.exists("Quotation",{"customer_address",doc}):
			quo_doc = frappe.get_doc("Quotation",{"customer_address",doc})
			return f"Cannot delete address linked with Quotation {quo_doc.name}"
		if frappe.db.exists("Sales Order",{"customer_address",doc}):
			so_doc = frappe.get_doc("Sales Order",{"customer_address",doc})
			return f"Cannot delete address linked with Sales Order {so_doc.name}"



@frappe.whitelist(allow_guest=True)
def get_user(doc):
	user_list = frappe.db.get_all('User', doc, filters={'email':frappe.session.user})
	return user_list

@frappe.whitelist(allow_guest=True)
def check_items_quantity(items):   
	try:
		from go1_webshop.go1_webshop.doctype.erp_settings.erp_settings import get_item_price_list
		if items and len(items) == 0:
			return 'Success'
		elif items and len(items) > 0:
			for item in items:		
				item_info = get_item_price_list(item.get("item_code"))
				if item_info and item_info.get("product_info").get("stock_qty") <= item.get('qty'):
					frappe.response.error_message = f"There Is No Stock Available For {item.get('item_name')}"
					return 'Failed'
		return 'Success'
	except Exception:
		frappe.log_error(title="go1_webshop.go1_webshop.api.check_items_quantity",message="")

@frappe.whitelist(allow_guest=True)
def update_user(doc):
	frappe.log_error("doc['last_Name']",doc["last_Name"])
	frappe.db.set_value('User', frappe.session.user,"last_name", doc["last_Name"])
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def insert_doc(**data):
    try:
        user = ""
        if data.get('data').get('doctype') == "Comment":
            user = frappe.session.user
            data['data']['comment_by'] = user        
        if data:
            insert_doc = frappe.get_doc({"doctype": data.get('data').get('doctype')})
            insert_doc.update(data.get('data'))
            value = insert_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return value
    except Exception as e:
        frappe.log_error("Error inserting document: " + str(e))
        return None

@frappe.whitelist(allow_guest=True)
def check_user_exists(email, password):
    try:
        user_exists = frappe.db.exists("User", {"email": email, "password": password})
        return {"exists": user_exists}
    except Exception as e:
        frappe.log_error("Error checking user existence: {0}".format(str(e)))
        return {"error": "An error occurred while checking user existence"}

@frappe.whitelist(allow_guest=True)
def get_list(doctype,fields=["name"],filters=None,page_no=1,page_size=20,order_by="creation desc",child_fields=None):
	limit_start = ((int(page_no) - 1) * int(page_size))
	try:
		list_items = frappe.get_all(doctype,
		filters=filters,
		fields=fields,
		order_by=order_by,
		start=limit_start,
		page_length=page_size,
		) 
		if child_fields and len(child_fields):
			for item in list_items:
				for child in child_fields:
					condition = "parent = '"+item.name+"'"
					query = """ SELECT name
						FROM `tab{child}` T 
						WHERE {condition} order by T.creation DESC""".format(condition=condition,
						child=child)
					child_field_name = child.casefold().replace(" ", "_")
					item[child_field_name] = frappe.db.sql(query,as_dict=1)
		frappe.response.message = list_items
		return list_items
	except:
		frappe.log_error("go1_webshop.api.get_list",frappe.get_traceback())
  

@frappe.whitelist(allow_guest=True)
def get_product_filter_data(query_args=None):
	"""
	Returns filtered products and discount filters.

	Args:
		query_args (dict): contains filters to get products list

	Query Args filters:
		search (str): Search Term.
		field_filters (dict): Keys include item_group, brand, etc.
		attribute_filters(dict): Keys include Color, Size, etc.
		start (int): Offset items by
		item_group (str): Valid Item Group
		from_filters (bool): Set as True to jump to page 1
	"""
	if isinstance(query_args, str):
		query_args = json.loads(query_args)

	query_args = frappe._dict(query_args)
	
	if query_args:
		search = query_args.get("search")
		field_filters = query_args.get("field_filters", {})
		attribute_filters = query_args.get("attribute_filters", {})
		start = cint(query_args.start) if query_args.get("start") else 0
		item_group = query_args.get("item_group")
		from_filters = query_args.get("from_filters")
		sort_by = query_args.get("sort_by") if query_args.get("sort_by") else None
	else:
		search, attribute_filters, item_group, from_filters = None, None, None, None
		field_filters = {}
		start = 0

	# if new filter is checked, reset start to show filtered items from page 1
	if from_filters:
		start = 0

	sub_categories = []
	if item_group:
		sub_categories = get_child_groups_for_website(item_group, immediate=True)

	engine = ProductQuery()

	try:
		result = engine.query(
			attribute_filters,
			field_filters,
			search_term=search,
			start=start,
			item_group=item_group,
			sort_by=sort_by
		)
		frappe.log_error("result",result)
	
	except Exception:
		frappe.log_error("Product query with filter failed")
		return {"exc": "Something went wrong!"}

	# discount filter data
	filters = {}
	discounts = result["discounts"]

	if discounts:
		filter_engine = ProductFiltersBuilder()
		filters["discount_filters"] = filter_engine.get_discount_filters(discounts)

	return {
		"items": result["items"] or [],
		"filters": filters,
		"settings": engine.settings,
		"sub_categories": sub_categories,
		"items_count": result["items_count"],
	}


@frappe.whitelist(allow_guest=True)
def get_guest_redirect_on_action():
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")


@frappe.whitelist()
def update_global_script(doc,method):
	global_script = frappe.get_value("Builder Settings","Builder Settings","custom_server_script")
	if global_script and doc.is_go1_webshop_item:
		if doc.page_data_script:
			if"\n# End Global Script\n" not in doc.page_data_script:
				doc.db_set('page_data_script',"\n# Start Global Script\n"+ global_script + "\n# End Global Script\n"+ doc.page_data_script)
		else:
			doc.db_set('page_data_script',"\n# Start Global Script\n"+global_script + "\n# End Global Script\n")
	frappe.db.commit()


@frappe.whitelist()
def update_global_script_builder_page(doc,method):
	old_doc = doc.get_doc_before_save()
	# global_script = frappe.get_value("Builder Settings","Builder Settings","custom_server_script")
	pages = frappe.db.get_all("Builder Page",pluck="name")
	for i in pages:
		page = frappe.get_doc("Builder Page",i)
		if doc.custom_server_script and page.is_go1_webshop_item:
			if page.page_data_script:
				if "\n# End Global Script\n" not in page.page_data_script:
					page.db_set('page_data_script',"\n# Start Global Script\n"+ doc.custom_server_script + "\n# End Global Script\n"+ page.page_data_script)
				else:
					parts = page.page_data_script.split("\n# End Global Script\n")
					page.db_set('page_data_script',"\n# Start Global Script\n"+ doc.custom_server_script + "\n# End Global Script\n"+ parts[1])
			else:
				page.db_set('page_data_script',"\n# Start Global Script\n"+doc.custom_server_script + "\n# End Global Script\n")
		frappe.db.commit()


@frappe.whitelist()
def insert_theme_register(full_name = None, email = None, phone = None, password = None):
	payload = {
				"full_name": full_name,
				"email": email,
				"phone":phone,
				"password":password
			}
	from go1_webshop.go1_webshop.doctype.erp_settings.erp_settings import get_external_url_details
	external_url_details = get_external_url_details("api", "insert_go1_theme_registration")
	frappe.log_error("external_url_details",external_url_details)
	try:
		response = requests.post(
									external_url_details.get("external_url"),
									headers = external_url_details.get("headers"), 
									data = json.dumps(payload)
								)
		response.raise_for_status()
		themes = response.json()
		if themes and themes.get("message"):
			output = themes.get("message")
			frappe.log_error("output", output)
			if output.get("api_key") and output.get("api_secret"):
				go1_theme_settings = frappe.get_doc("Go1 Webshop Theme Settings")
				go1_theme_settings.api_key = output.get("api_key")
				go1_theme_settings.api_secret = output.get("api_secret")
				go1_theme_settings.save(ignore_permissions = True)
		return "Success"
	except:
		frappe.log_error("Error in api.insert_theme_register", frappe.get_traceback())

@frappe.whitelist()
def login_theme_registration(email = None, password = None):
	payload = {
				"usr": email,
				"pwd":password
			}
	from go1_webshop.go1_webshop.doctype.erp_settings.erp_settings import get_external_url_details
	external_url_details = get_external_url_details("api", "login_go1_theme_registration")
	frappe.log_error("external_url_details",external_url_details)
	try:
		response = requests.post(
									external_url_details.get("external_url"),
									headers = external_url_details.get("headers"), 
									data = json.dumps(payload)
								)
		response.raise_for_status()
		themes = response.json()
		if themes and themes.get("message"):
			output = themes.get("message")
			frappe.log_error("output", output)
			if output.get("status") == "Success":
				if output.get("message")["api_key"] and output.get("message")["api_secret"]:
					go1_theme_settings = frappe.get_doc("Go1 Webshop Theme Settings")
					go1_theme_settings.api_key = output.get("message")["api_key"]
					go1_theme_settings.api_secret = output.get("message")["api_secret"]
					go1_theme_settings.save(ignore_permissions = True)
			return output.get("status")
	except:
		frappe.log_error("Error in api.insert_theme_register", frappe.get_traceback())


@frappe.whitelist()
def update_website_item_route(doc,method):
	if doc.route:
		doc.route = doc.route.replace("/","-")