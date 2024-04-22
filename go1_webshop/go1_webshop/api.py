from frappe import _
import frappe

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
  
