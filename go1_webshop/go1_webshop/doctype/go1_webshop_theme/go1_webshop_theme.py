# Copyright (c) 2024, tridotstech and contributors
# For license information, please see license.txt

import frappe
import os
from frappe.model.document import Document


class Go1WebshopTheme(Document):
	def on_update(self):
		css_content = log_css_template(self.name)
		self.create_theme_directory(css_content)

	def create_theme_directory(self, css_content):
		theme_route = self.get("theme_route")
		
		if theme_route:
			directory_path = os.path.join(frappe.get_module_path("go1_webshop"), theme_route.replace(' ', '_').lower())
			theme_path = os.path.join(directory_path, "themes",theme_route)
			if not os.path.exists(theme_path):
				os.makedirs(theme_path)
			new_file_path = os.path.join(theme_path, "theme.css")
			if os.path.exists(new_file_path):
				with open(new_file_path, 'w') as css_data:
					css_data.write(css_content)
					frappe.log_error("CSS Content Updated", css_data)
			
		else:
			frappe.log_error("Theme route is not set for the theme", title="Theme Route Error")


@frappe.whitelist()
def get_curnet_doc(webshop_settings):
	theme = frappe.get_doc("Go1 Webshop Theme", {"theme_route":webshop_settings})
	frappe.log_error("theme",theme)
	return theme


@frappe.whitelist()
def log_css_template(doc_name):
	doc = frappe.get_doc("Go1 Webshop Theme", doc_name)
	doc_values = doc.as_dict()
	system_fields = {"doctype", "name", "owner", "creation", "modified", "modified_by", "idx", "docstatus"}
	filtered_doc_values = {key: value for key, value in doc_values.items() if key not in system_fields}
	template_path = "go1_webshop/public/root.css"
	css_content = frappe.get_template(template_path).render(doc = filtered_doc_values)
	# frappe.log_error(message = css_content, title = "CSS Template Content")
	return css_content


@frappe.whitelist()
def get_css_content(theme):
    module_path = frappe.get_module_path("go1_webshop")
    new_file_path = os.path.join(module_path, "themes", theme, "theme.css")
    if os.path.exists(new_file_path):
        with open(new_file_path, 'r') as css_data:
            return css_data.read()