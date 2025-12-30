from frappe import _
import frappe
import json
import requests
from frappe import _
from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from frappe.utils import cint
from go1_webshop.go1_webshop.query import ProductQuery
# from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website

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
	frappe.db.set_value('User', frappe.session.user,"user_image", doc["profile_image"])
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
	frappe.log_error("query_args",query_args)
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


def get_child_groups_for_website(item_group_name, immediate=False, include_self=False):
	"""Returns child item groups *excluding* passed group."""
	item_group = frappe.get_cached_value("Item Group", item_group_name, ["lft", "rgt"], as_dict=1)
	filters = {"lft": [">", item_group.lft], "rgt": ["<", item_group.rgt], "show_in_website": 1}

	if immediate:
		filters["parent_item_group"] = item_group_name

	if include_self:
		filters.update({"lft": [">=", item_group.lft], "rgt": ["<=", item_group.rgt]})

	return frappe.get_all("Item Group", filters=filters, fields=["name", "route","image"], order_by="creation")

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

@frappe.whitelist(allow_guest=True)
def insert_customer(first_name,email,mobile_no,new_password):
	if frappe.db.get_all("Customer",filters={"email_id":email}):
		return {"status":"Failed","message":"Email Id is already registered."}
	if frappe.db.get_all("Customer",filters={"mobile_no":mobile_no}):
		return {"status":"Failed","message":"Mobile No is already registered."}
	customer_doc = frappe.new_doc("Customer")
	customer_doc.customer_name = first_name
	customer_doc.custom_phone_number = mobile_no
	customer_doc.save(ignore_permissions=True)
	contact_doc = frappe.new_doc("Contact")
	contact_doc.first_name = first_name
	contact_doc.email_id = email
	contact_doc.mobile_no = mobile_no
	contact_doc.is_primary_contact = 1
	contact_doc.append("email_ids",{"email_id":email,"is_primary":1})
	contact_doc.append("phone_nos",{"phone":mobile_no,"is_primary_mobile_no":1})
	contact_doc.append("links",{"link_doctype":"Customer","link_name":customer_doc.name})
	contact_doc.save(ignore_permissions=True)
	user_doc = frappe.new_doc("User")
	user_doc.email = email
	user_doc.first_name = first_name
	user_doc.mobile_no = mobile_no
	user_doc.new_password = new_password
	user_doc.save(ignore_permissions=True)
	customer_doc.append("portal_users",{"user":user_doc.name})
	customer_doc.customer_primary_contact = contact_doc.name
	customer_doc.save(ignore_permissions=True)
	return {"status":"Success"}

@frappe.whitelist(allow_guest=True)
def get_variant_details(item_code,attributes):
	try:
		item_code = frappe.form_dict.get("item_code")
		attributes = frappe.form_dict.get("attributes")
		args = {attr: value for attr, value in attributes.items()}
		# Find existing variant
		variant_item_code = None
		variants = frappe.get_all("Item", 
			filters={
				"variant_of": item_code,
				"disabled": 0
			},
			pluck="name"
		)
		for variant in variants:
			v_attributes = frappe.get_all("Item Variant Attribute",filters={"parent": variant},order_by='idx',fields=["attribute", "attribute_value"])
			variant_attributes = {attr.attribute: attr.attribute_value for attr in v_attributes}
			if variant_attributes == args:
				variant_item_code =  variant
		if variant_item_code:
			website_item = frappe.db.get_value("Website Item", filters={"item_code":variant_item_code})
			if not website_item:
				frappe.response["message"] =  {
					"success": "Failed",
					"message": _("No Website item found"),
					"template_item": item_code,
					"requested_attributes": attributes
				}
			frappe.log_error("website_item",website_item)
			if website_item:
				try:
					
					web_item = frappe.get_doc('Website Item', website_item)
					context = web_item.as_dict()
					web_item.get_context(context)
					context['cart_count'] = 0
					user_info = None
					frappe.log_error("frappe.session.user",frappe.session.user)
					if frappe.session.user!="Guest":
						user_info = frappe.db.sql(f"""
						SELECT C.name 
						FROM `tabCustomer` C 
						INNER JOIN `tabPortal User` PU ON C.name = PU.parent 
						WHERE PU.user = '{frappe.session.user}'
					""", as_dict=1)
					if user_info and frappe.db.exists("Quotation", {"party_name": user_info[0]["name"], "order_type": "Shopping Cart", "status": "draft"}):
						quotation_doc = frappe.db.get_value("Quotation", {"status":"Draft", "quotation_to": "Customer", "party_name": user_info[0]["name"]}, "name")
						if frappe.db.exists("Quotation Item", {"parent": quotation_doc, "item_code": web_item.item_code}):
						  context['cart_count'] = int(frappe.db.get_value("Quotation Item", {"parent": quotation_doc, "item_code": web_item.item_code}, "qty"))
					frappe.response["message"] =  {
						"success": "Sucess",
						"message":context
					}
				except Exception:
					frappe.log_error(title="variats_details",message=frappe.get_traceback())
					
			
		else:
			frappe.response["message"] =  {
				"success": "Failed",
				"message": _("No variant found for the given attributes"),
				"template_item": item_code,
				"requested_attributes": attributes
			}
	except Exception:
		frappe.log_error(title="variats_details",message=frappe.get_traceback())
		 
