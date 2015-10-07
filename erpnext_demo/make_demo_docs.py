import frappe, os

from frappe.core.page.data_import_tool.data_import_tool import export_json

def export_demo_masters():
	# pre-process
	frappe.db.sql("update tabItem set default_bom=''")

	doctypes = (
		"Fiscal Year",
		"Holiday List",
		"Item",
		"Product Bundle",
		"Operation",
		"Workstation",
		"BOM",
		"Item Price",
		"Customer",
		"Supplier",
		"Contact",
		"Address",
		"Lead",
		"User",
		"Employee",
		"Salary Structure",
		"Currency Exchange",
		("Account", {"account_type": "Tax", "is_group": 0}),
		("Warehouse", {"name": "Supplier - WP"}),
		"Sales Taxes and Charges Template",
		"Purchase Taxes and Charges Template",
		"Shipping Rule")
	export_data(doctypes)

def export_data(dt):
	if not isinstance(dt, (tuple, list)):
		dt = [dt]

	for doctype in dt:
		filters=None
		if isinstance(doctype, (tuple, list)):
			doctype, filters = doctype
		export_json(doctype, get_json_path(doctype), filters=filters)

def get_json_path(doctype):
	return os.path.join(os.path.dirname(__file__), "demo_docs", doctype+".json")

