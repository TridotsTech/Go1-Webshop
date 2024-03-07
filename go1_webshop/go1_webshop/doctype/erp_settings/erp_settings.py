# Copyright (c) 2024, tridotstech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from webshop.webshop.doctype.override_doctype.item_group import WebshopItemGroup

class ErpSettings(Document):
    def get_item_list(self,item_group,attribute_filters):
        try:
            from webshop.webshop.api import get_product_filter_data
            frappe.log_error(title="item_group",message={"item_group":item_group,"attribute_filters":attribute_filters})
            # frappe.log_error(title="attribute_filters",message={"filter":attribute_filters,"type":type(json.loads(attribute_filters))}) json.loads(attribute_filters) if attribute_filters else
            if item_group:
                return get_product_filter_data(query_args={"field_filters":{},"attribute_filters": json.loads(attribute_filters) if attribute_filters else "","item_group":item_group,"start":None,"from_filters":False})
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
def get_item_price_list(item_code):
    from webshop.webshop.shopping_cart.product_info import (
        get_product_info_for_website,
    )
    return get_product_info_for_website(
        item_code, skip_quotation_creation=True
    )
