# Copyright (c) 2024, Tridots and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from webshop.webshop.doctype.override_doctype.item_group import WebshopItemGroup
# from webshop.webshop.api import get_product_filter_data
from go1_builder.go1_builder.api import get_product_filter_data
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
            frappe.log_error("query_args",query_args)
            if item_group:
                return get_product_filter_data(query_args)
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

class ItemGroupInfo():
    def validate(self):
        super(WebshopItemGroup, self).get_context()

# group = ItemGroupInfo()
# group.validate()
    # pass
# def get_item_price():
#     return 'Success'
@frappe.whitelist()
def get_item_price_list(item_code):
    from webshop.webshop.shopping_cart.product_info import (
        get_product_info_for_website,
    )
    return get_product_info_for_website(
        item_code, skip_quotation_creation=True
    )

@frappe.whitelist(allow_guest=True)
def get_cart_items():
    from webshop.webshop.shopping_cart.cart import get_cart_quotation
    cart_result =  get_cart_quotation()
    for x in cart_result.get("doc").get("items"):
        x.qty = x.get_formatted('qty')
        x.amount = x.get_formatted('amount')
        x.rate = x.get_formatted('rate')
    cart_result.get("doc").total = cart_result.get("doc").get_formatted('total')
    cart_result.get("doc").grand_total = cart_result.get("doc").get_formatted('grand_total')
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
                                   INNER JOIN 
                                     `tabWebsite Item` I ON I.name = WI.website_item
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
    
