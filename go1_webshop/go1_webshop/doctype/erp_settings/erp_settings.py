# Copyright (c) 2024, Tridots and contributors
# For license information, please see license.txt

import frappe
import json
import requests
from frappe import _
from frappe.model.document import Document
from webshop.webshop.doctype.override_doctype.item_group import WebshopItemGroup
# from webshop.webshop.api import get_product_filter_data
from go1_webshop.go1_webshop.api import get_product_filter_data
class ErpSettings(Document):
	def get_item_list(self,item_group,attribute_filters,sort_by=None,start=None):
		try:
			attribute_filters = json.loads(attribute_filters) if attribute_filters else ""
			query_args={"field_filters":{},"attribute_filters": attribute_filters,
						"item_group":item_group,"start":None,"from_filters":False,"start":start}
			sort_value = ""
			if sort_by:
				if sort_by == "name_asc":
					sort_value = "web_item_name ASC" 
				if sort_by == "name_desc":
					sort_value = "web_item_name DESC" 
				if sort_by == "relevence":
					sort_value = "`tabWebsite Item`.modified DESC"
			query_args['sort_by'] = sort_value
			if item_group:
				category_data = get_product_filter_data(query_args)
				for x in category_data.get("items"):
					x.discount_label = ""
					if x.discount_percent:
						x.discount_label = str(int(x.discount_percent))+"% OFF"
				return category_data
			else:
				return []
		except Exception:
			frappe.log_error("get_item_list",frappe.get_traceback())
			return []
	# def item_group_info(self,context):
		# WebshopItemGroup
		# return get_context(context)
	def get_cart_items(self):
		from webshop.webshop.shopping_cart.cart import get_cart_quotation
		cart_result =  get_cart_quotation()
		for x in cart_result.get("doc").get("items"):
			x.qty = x.get_formatted('qty')
			x.amount = x.get_formatted('amount')
			x.rate = x.get_formatted('rate')
		cart_result.get("doc").total = cart_result.get("doc").get_formatted('total')
		cart_result.get("doc").grand_total = cart_result.get("doc").get_formatted('grand_total')
		return cart_result
	def get_item_price(self,item_code):
		from webshop.webshop.shopping_cart.product_info import (
			get_product_info_for_website,
		)
		return get_product_info_for_website(
			item_code, skip_quotation_creation=True
		) 
		
	def get_quotation_info(self):
		from webshop.webshop.shopping_cart.cart import get_cart_quotation 
		return get_cart_quotation()
	
	def search_products(self,text):
		from webshop.templates.pages.product_search import search 
		return search(query=text)

	def redirect_login(self,redirect_url=None):
		frappe.local.flags.redirect_location = '/login'+("?redirect_url="+redirect_url) if redirect_url else ""
		raise frappe.Redirect
		
	def get_item_reviews(self,website_item):
		from webshop.webshop.doctype.item_review.item_review import get_item_reviews as _get_item_reviews
		reviews_data =  _get_item_reviews(website_item)
		reviews_data["reviews"] = frappe.db.get_all("Item Review",filters={"website_item":website_item},fields=['*'])
		if reviews_data.get("reviews"):
			for x in reviews_data.get("reviews"):
				x.rating_value = x.rating*5
			reviews_data.average_ratings = reviews_data.average_rating*5 if not reviews_data.average_rating<5 else round(reviews_data.average_rating,1)
		reviews_data.stars_percetange = {"star1":0,"star2":0,"star3":0,"star4":0,"star5":0}
		for x in reviews_data.get("reviews"):
			if (x.rating*5) == 1:
				reviews_data.stars_percetange["star1"] = reviews_data.stars_percetange["star1"]+1
			if (x.rating*5) == 2:
				reviews_data.stars_percetange["star2"] = reviews_data.stars_percetange["star2"]+1
			if (x.rating*5) == 3:
				reviews_data.stars_percetange["star3"] = reviews_data.stars_percetange["star3"]+1
			if (x.rating*5) == 4:
				reviews_data.stars_percetange["star4"] = reviews_data.stars_percetange["star4"]+1
			if (x.rating*5) == 5:
				reviews_data.stars_percetange["star5"] = reviews_data.stars_percetange["star5"]+1
		if reviews_data.total_reviews>0:
			reviews_data.stars_percetange["star1"] = int((reviews_data.stars_percetange["star1"]/reviews_data.total_reviews)*100)
			reviews_data.stars_percetange["star2"] = int((reviews_data.stars_percetange["star2"]/reviews_data.total_reviews)*100)
			reviews_data.stars_percetange["star3"] = int((reviews_data.stars_percetange["star3"]/reviews_data.total_reviews)*100)
			reviews_data.stars_percetange["star4"] = int((reviews_data.stars_percetange["star4"]/reviews_data.total_reviews)*100)
			reviews_data.stars_percetange["star5"] = int((reviews_data.stars_percetange["star5"]/reviews_data.total_reviews)*100)
		return reviews_data


	def get_group_items(self, item_group = None, item_code = None, user_name = None,page_length=12):
		filters = {"item_group":item_group,"published":1}
		if item_code:
			filters["item_code"] = ["!=", item_code]
		item_list = frappe.db.get_all("Website Item",
										fields=["name","item_name as web_item_name","item_code","website_image","route"],
										filters=filters,
										limit_page_length=page_length)
		self.get_items_price(item_list = item_list, user_name = user_name)
		for x in item_list:
			x.discount_label = ""
			if x.discount_percent:
				x.discount_label = str(int(x.discount_percent))+"% OFF"
		return item_list


	def get_cart_count(self, user_name = None, item_code = None):
		if user_name:
			if frappe.db.exists("Quotation", {"status":"Draft", "quotation_to": "Customer", "party_name": user_name}):
				quotation_doc = frappe.db.get_value("Quotation", {"status":"Draft", "quotation_to": "Customer", "party_name": user_name}, "name")
				if frappe.db.exists("Quotation Item", {"parent": quotation_doc, "item_code": item_code}):
					cart_count = int(frappe.db.get_value("Quotation Item", {"parent": quotation_doc, "item_code": item_code}, "qty"))
					return cart_count
		   

	def get_item_recomemented_items(self,website_item,page_length=12,user_name=None):
		rec_items = frappe.db.get_all("Recommended Items",
									fields=['website_item_image',"item_code","website_item_name as web_item_name","route","website_item_thumbnail as website_image","website_item"],
									filters={"parent":website_item},
									limit_page_length=page_length)
		self.get_items_price(item_list = rec_items,user_name=user_name)
		for x in rec_items:
			x.discount_label = ""
			if x.discount_percent:
				x.discount_label = str(int(x.discount_percent))+"% OFF"    
		return rec_items
	def get_items_price(self, item_list = None, user_name = None):
		try:
			if item_list:
				for x in item_list:
					web_item = frappe.get_doc("Website Item", {"route":x.route})
					x.enable_wishlist = frappe.db.get_single_value("Webshop Settings","enable_wishlist")
					x.wished = False
					if frappe.session.user != "Guest":
						check_wishlist = frappe.db.get_all("Wishlist Item",filters={"item_code":web_item.item_code,"parent":frappe.session.user})
						if check_wishlist:
							x.wished = True
					# if not x.website_item_thumbnail:
					# 	x.website_item_thumbnail = "/files/go1logo-color.svg"
					price_info = self.get_item_price(x.item_code)
					if price_info and price_info.get("product_info"):
						x.in_stock = price_info.get("product_info").get("in_stock")
						if price_info.get("product_info").get("price"):
							x.formatted_price = price_info.get("product_info").get("price").get("formatted_price")
							x.discount_percent = price_info.get("product_info").get("price").get("discount_percent")
							x.formatted_mrp = price_info.get("product_info").get("price").get("formatted_mrp")
					# if not x.website_image:
					# 	x.website_image = "/files/gf_no_image.png"
					related_item_offers = frappe.db.get_all("Website Offer", filters={"parent": web_item.name}, fields=["offer_title"])
					x.offer_title = related_item_offers[0].offer_title if related_item_offers else None
					x.cart_count = 0
					if user_name:
						if frappe.db.exists("Quotation", {"status":"Draft", "quotation_to": "Customer", "party_name": user_name}):
							quotation_doc = frappe.db.get_value("Quotation", {"status":"Draft", "quotation_to": "Customer", "party_name": user_name}, "name")
							if frappe.db.exists("Quotation Item", {"parent": quotation_doc, "item_code": web_item.item_code}):
								x.cart_count = int(frappe.db.get_value("Quotation Item", {"parent": quotation_doc, "item_code": web_item.item_code}, "qty"))
					if not x.item_description:
						x.item_description = web_item.description
					if not x.description:
						x.description = web_item.description
					
			return item_list
		except:
			frappe.error_log("Error in erp_settings.get_recommented_items", frappe.get_traceback())

	def get_item_details(self,route,user_name,page_length):
		try:
			web_item = frappe.get_doc('Website Item', {"route":route})
			reviews = self.get_item_reviews(web_item.name)
			w_context = web_item
			web_item.get_context(w_context)
			details = [w_context]
			parents = w_context.parents
			recommended_items = self.get_item_recomemented_items(website_item=web_item.name,page_length=page_length, user_name = user_name)
			shopping_cart_data = w_context.get("shopping_cart")
			if shopping_cart_data:
				if shopping_cart_data.price:
					shopping_cart_data.price.discount_label = ""
					if shopping_cart_data.price.discount_percent:
						shopping_cart_data.price.discount_label = str(int(shopping_cart_data.price.discount_percent.discount_percent))+"% OFF"
			cart_count = self.get_cart_count(user_name = user_name, item_code = web_item.item_code)
			related_items = self.get_group_items(item_group = web_item.item_group, item_code = web_item.item_code, user_name = user_name,page_length=page_length)
			return_obj =  {"details":details,"shopping_cart_data":shopping_cart_data,
					"cart_count":cart_count,"related_items":related_items,
					"recommended_items":recommended_items,
					"parents":parents}
			frappe.log_error("return_obj",return_obj)
			return return_obj
		except:
			frappe.error_log("Error in erp_settings.get_item_details", frappe.get_traceback())


	def get_template_category_details(self, theme_route = None):
		external_url_details = get_external_url_details("api", "get_template_category_details")
		# user_name = frappe.session.user
		user_name = "abishek@tridotstech.com"
		payload = {
					"user": user_name
				}
		if theme_route:
			payload["theme_route"] = theme_route
		try:
			response = requests.post(
										external_url_details.get("external_url"),
										headers = external_url_details.get("headers"), 
										json = payload
									)
			response.raise_for_status()
			themes = response.json()
			return themes.get('message', [])
		except requests.exceptions.RequestException as e:
			frappe.throw(_('Error in erp_settings.get_template_category_details').format(str(e)))
		except:
			frappe.log_error("Error in erp_settings.get_template_category_details", frappe.get_traceback())


	def get_theme_details(self, theme_route = None):
		external_url_details = get_external_url_details("api", "get_themes_details")
		# user_name = frappe.session.user
		user_name = "abishek@tridotstech.com"
		payload = {
					"user": user_name
				}
		if theme_route:
			payload["theme_route"] = theme_route
		try:
			response = requests.post(
										external_url_details.get("external_url"),
										headers = external_url_details.get("headers"), 
										json = payload
									)
			response.raise_for_status()
			themes = response.json()
			if themes and themes.get("message"):
				data = themes.get("message")
				for theme in data:
					theme["is_installed"] = 1 if frappe.db.get_all("Go1 Webshop Theme", filters = {"name": theme.get("name")}) else 0
				return data
			return themes.get('message', [])
		except:
			frappe.log_error("Error in erp_settings.get_theme_details", frappe.get_traceback())
			return []


	def check_installed_theme(self, theme_route = None):
		is_installed = "Download & Install"
		if frappe.db.exists("Go1 Webshop Theme", {"theme_route": theme_route}):
			is_installed = "Activate"
		return is_installed


def get_external_url_details(file_name, api_name):
	webshop_theme_settings = frappe.get_single("Go1 Webshop Theme Settings")
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"token {webshop_theme_settings.api_key}:{webshop_theme_settings.api_secret}"
	}
	external_url = f"{webshop_theme_settings.url}/api/method/go1_webshop_theme.go1_webshop_theme.{file_name}.{api_name}"

	return {
			"external_url": external_url,
			"headers": headers
		}


class ItemGroupInfo():
	def validate(self):
		super(WebshopItemGroup, self).get_context()

@frappe.whitelist()
def get_item_price_list(item_code):
	from webshop.webshop.shopping_cart.product_info import (
		get_product_info_for_website,
	)
	return get_product_info_for_website(
		item_code, skip_quotation_creation=True
	)

@frappe.whitelist()
def get_cart_items():
	from webshop.webshop.shopping_cart.cart import get_cart_quotation
	cart_result =  get_cart_quotation()
	for x in cart_result.get("doc").get("items"):
		x.qty = x.get_formatted('qty')
		x.amount = x.get_formatted('amount')
		x.rate = x.get_formatted('rate')
		x.image = frappe.db.get_value("Website Item", {"item_code":x.item_code}, "website_image")
	cart_result.get("doc").total = cart_result.get("doc").get_formatted('total')
	cart_result.get("doc").grand_total = cart_result.get("doc").get_formatted('grand_total')
	default_currency = frappe.db.get_single_value('Global Defaults',"default_currency")
	currency_symbol = frappe.db.get_value("Currency",default_currency,"symbol")
	cart_result['currency_symbol'] = currency_symbol
	return cart_result

def get_item_price(item_code):
	from webshop.webshop.shopping_cart.product_info import (
		get_product_info_for_website,
	)
	return get_product_info_for_website(
		item_code, skip_quotation_creation=True
	)
	
@frappe.whitelist(allow_guest=True)
def wishlist_items():
	wishlist_items = frappe.db.sql(""" SELECT I.item_code,I.name,I.item_name as web_item_name,I.website_image,I.route
										FROM `tabWishlist Item` WI
										INNER JOIN `tabWebsite Item` I ON I.name = WI.website_item
										WHERE WI.parent=%(user)s
									""",{"user":frappe.session.user},as_dict=1)
	if wishlist_items:
		for x in wishlist_items:
			if not x.website_item_thumbnail:
				x.website_item_thumbnail = "/files/go1logo-color.svg"
			price_info = get_item_price(x.item_code)
			if price_info and price_info.get("product_info"):
				x.in_stock = price_info.get("product_info").get("in_stock")
				if price_info.get("product_info").get("price"):
					x.formatted_price = price_info.get("product_info").get("price").get("formatted_price")
	return wishlist_items

@frappe.whitelist(allow_guest=True)
def get_item_list(item_group,attribute_filters,sort_by=None,start=None):
	try:                  
		attribute_filters = json.loads(attribute_filters) if attribute_filters else ""
		query_args={"field_filters":{},"attribute_filters": attribute_filters,"item_group":item_group,"start":None,"from_filters":False,"start":start}
		sort_value = ""
		if sort_by:
			if sort_by == "name_asc":
				sort_value = "web_item_name ASC" 
			if sort_by == "name_desc":
				sort_value = "web_item_name DESC" 
			if sort_by == "relevence":
				sort_value = "`tabWebsite Item`.modified DESC"
		query_args['sort_by'] = sort_value
		frappe.log_error("query_args",query_args)
		if item_group:
			return get_product_filter_data(query_args)
		else:
			return []
	except Exception:
		frappe.log_error("get_item_list",frappe.get_traceback())
		return []

@frappe.whitelist()
def add_review(title,comment,rating,web_item):
	from datetime import datetime
	doc = frappe.new_doc("Item Review")
	doc.update(
		{
			"user": frappe.session.user,
			"customer": get_customer(),
			"website_item": web_item,
			"item": frappe.db.get_value("Website Item", web_item, "item_code"),
			"review_title": title,
			"rating": rating,
			"comment": comment,
		}
	)
	doc.published_on = datetime.today().strftime("%d %B %Y")
	doc.save()

def get_customer(silent=False):
	from frappe.contacts.doctype.contact.contact import get_contact_name

	"""
	silent: Return customer if exists else return nothing. Dont throw error.
	"""
	user = frappe.session.user
	contact_name = get_contact_name(user)
	customer = None

	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
		for link in contact.links:
			if link.link_doctype == "Customer":
				customer = link.link_name
				break

	if customer:
		return frappe.db.get_value("Customer", customer)
	elif silent:
		return None
	else:
		# should not reach here unless via an API
		frappe.throw(
			_("You are not a verified customer yet. Please contact us to proceed."), exc=UnverifiedReviewer
		)
	
