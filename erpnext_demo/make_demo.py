# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

import frappe, os
import frappe.utils

from frappe.core.page.data_import_tool.data_import_tool import import_doc
from erpnext_demo.simulate import simulate
from erpnext_demo.make_demo_docs import get_json_path
from erpnext_demo import settings

# fix price list
# fix fiscal year

def make():
	frappe.flags.mute_emails = True
	setup()
	frappe.set_user("Administrator")
	simulate()

def setup():
	complete_setup()
	make_customers_suppliers_contacts()
	show_item_groups_in_website()
	make_items()
	make_price_lists()
	make_users_and_employees()
	make_bank_account()
	# make_opening_stock()
	# make_opening_accounts()

	# make_tax_accounts()
	make_tax_masters()
	make_shipping_rules()
	if "shopping_cart" in frappe.get_installed_apps():
		enable_shopping_cart()

	frappe.clear_cache()

def install():
	print "Creating Fresh Database..."
	from frappe.install_lib.install import Installer
	from frappe import conf
	inst = Installer('root')
	inst.install(conf.demo_db_name, verbose=1, force=1)

def complete_setup():
	print "Complete Setup..."
	from erpnext.setup.page.setup_wizard.setup_wizard import setup_account
	setup_account({
		"first_name": "Test",
		"last_name": "User",
		"email": "test_demo@erpnext.com",
		"company_tagline": "Wind Mills for a Better Tomorrow",
		"password": "test",
		"fy_start_date": "2015-01-01",
		"fy_end_date": "2015-12-31",
		"industry": "Manufacturing",
		"company_name": settings.company,
		"chart_of_accounts": "Standard",
		"company_abbr": settings.company_abbr,
		"currency": settings.currency,
		"timezone": settings.time_zone,
		"country": settings.country,
		"language": "english"
	})

	# home page should always be "start"
	website_settings = frappe.get_doc("Website Settings", "Website Settings")
	website_settings.home_page = "start"
	website_settings.save()

	import_data("Fiscal Year")
	import_data("Holiday List")

	frappe.clear_cache()

def show_item_groups_in_website():
	"""set show_in_website=1 for Item Groups"""
	products = frappe.get_doc("Item Group", "Products")
	products.show_in_website = 1
	products.save()

def make_items():
	import_data("Item")
	import_data("Warehouse")
	import_data("Product Bundle")
	import_data("Workstation")
	import_data("Operation")
	import_data("BOM", submit=True)
	fix_attachments()

def make_price_lists():
	import_data("Currency Exchange")
	add_item_price()

def make_customers_suppliers_contacts():
	import_data(["Account", "Customer", "Supplier", "Contact", "Address", "Lead"])

def make_users_and_employees():
	frappe.db.set_value("HR Settings", None, "emp_created_by", "Naming Series")
	frappe.db.commit()

	import_data(["User", "Employee", "Salary Structure"])

def make_bank_account():
	ba = frappe.get_doc({
		"doctype": "Account",
		"account_name": settings.bank_name,
		"account_type": "Bank",
		"is_group": 0,
		"parent_account": "Bank Accounts - " + settings.company_abbr,
		"company": settings.company
	}).insert()

	frappe.set_value("Company", settings.company, "default_bank_account", ba.name)
	frappe.db.commit()

def make_tax_masters():
	import_data("Sales Taxes and Charges Template")
	import_data("Purchase Taxes and Charges Template")

def make_shipping_rules():
	import_data("Shipping Rule")

def enable_shopping_cart():
	# import
	path = os.path.join(os.path.dirname(__file__), "demo_docs", "Shopping Cart Settings.json")
	import_doc(path)

	# enable
	settings = frappe.get_doc("Shopping Cart Settings")
	settings.enabled = 1
	settings.save()

def import_data(dt, submit=False, overwrite=False):
	if not isinstance(dt, (tuple, list)):
		dt = [dt]

	for doctype in dt:
		import_doc(get_json_path(doctype), submit=submit, overwrite=overwrite)

def add_item_price():
	frappe.db.sql("delete from `tabItem Price`")

	standard_selling = {
		"Base Bearing Plate": 28,
		"Base Plate": 21,
		"Bearing Assembly": 300,
		"Bearing Block": 14,
		"Bearing Collar": 103.6,
		"Bearing Pipe": 63,
		"Blade Rib": 46.2,
		"Disc Collars": 42,
		"External Disc": 56,
		"Internal Disc": 70,
		"Shaft": 340,
		"Stand": 400,
		"Upper Bearing Plate": 300,
		"Wind Mill A Series": 320,
		"Wind Mill A Series with Spare Bearing": 750,
		"Wind MIll C Series": 400,
		"Wind Turbine": 400,
		"Wing Sheet": 30.8
	}

	standard_buying = {
		"Base Bearing Plate": 20,
		"Base Plate": 28,
		"Base Plate Un Painted": 16,
		"Bearing Block": 13,
		"Bearing Collar": 96.4,
		"Bearing Pipe": 55,
		"Blade Rib": 38,
		"Disc Collars": 34,
		"External Disc": 50,
		"Internal Disc": 60,
		"Shaft": 250,
		"Stand": 300,
		"Upper Bearing Plate": 200,
		"Wing Sheet": 25
	}

	for price_list in ("standard_buying", "standard_selling"):
		for item, rate in locals().get(price_list).iteritems():
			frappe.get_doc({
				"doctype": "Item Price",
				"price_list": price_list.replace("_", " ").title(),
				"item_code": item,
				"selling": 1 if price_list=="standard_selling" else 0,
				"buying": 1 if price_list=="standard_buying" else 0,
				"price_list_rate": rate,
				"currency": "USD"
			}).insert()

def fix_attachments():
	"""Create attachment objects for image fields"""
	for item in frappe.get_all("Item", fields=("name", "website_image")):
		if item.website_image:
			item_doc = frappe.get_doc("Item", item.name)
			item_doc.make_thumbnail()
			item_doc.db_set("thumbnail", item_doc.thumbnail)

