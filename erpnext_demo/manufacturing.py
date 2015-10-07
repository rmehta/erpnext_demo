# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils.make_random import how_many, can_make
from frappe.desk import query_report
from frappe.utils import cstr
from erpnext_demo import settings

def run_manufacturing(current_date):
	from erpnext.projects.doctype.time_log.time_log import NotSubmittedError, OverlapError

	ppt = frappe.get_doc("Production Planning Tool", "Production Planning Tool")
	ppt.company = settings.company
	ppt.use_multi_level_bom = 1
	ppt.purchase_request_for_warehouse = "Stores - {}".format(settings.company_abbr)
	ppt.run_method("get_open_sales_orders")
	ppt.run_method("get_items_from_so")
	ppt.run_method("raise_production_order")
	ppt.run_method("raise_purchase_request")
	frappe.db.commit()

	# submit production orders
	for pro in frappe.db.get_values("Production Order", {"docstatus": 0}, "name"):
		b = frappe.get_doc("Production Order", pro[0])
		b.wip_warehouse = "Work in Progress - WP"
		b.submit()
		frappe.db.commit()

	# submit material requests
	for pro in frappe.db.get_values("Material Request", {"docstatus": 0}, "name"):
		b = frappe.get_doc("Material Request", pro[0])
		b.submit()
		frappe.db.commit()

	# stores -> wip
	if can_make("Stock Entry for WIP"):
		for pro in query_report.run("Open Production Orders")["result"][:how_many("Stock Entry for WIP")]:
			make_stock_entry_from_pro(pro[0], "Material Transfer for Manufacture", current_date)

	# wip -> fg
	if can_make("Stock Entry for FG"):
		for pro in query_report.run("Production Orders in Progress")["result"][:how_many("Stock Entry for FG")]:
			make_stock_entry_from_pro(pro[0], "Manufacture", current_date)

	# submit time logs
	for time_log in frappe.get_all("Time Log", ["name"], {"docstatus": 0,
		"production_order": ("!=", ""), "to_time": ("<", current_date)}):
		time_log = frappe.get_doc("Time Log", time_log.name)
		try:
			time_log.submit()
			frappe.db.commit()
			print time_log.name
		except OverlapError:
			pass

def make_stock_entry_from_pro(pro_id, purpose, current_date):
	from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry
	from erpnext.stock.stock_ledger import NegativeStockError
	from erpnext.stock.doctype.stock_entry.stock_entry import IncorrectValuationRateError, \
		DuplicateEntryForProductionOrderError, OperationsNotCompleteError

	try:
		st = frappe.get_doc(make_stock_entry(pro_id, purpose))
		st.posting_date = current_date
		st.fiscal_year = cstr(current_date.year)
		for d in st.get("items"):
			d.cost_center = "Main - " + settings.company_abbr
		st.insert()
		frappe.db.commit()
		st.submit()
		frappe.db.commit()
	except (NegativeStockError, IncorrectValuationRateError, DuplicateEntryForProductionOrderError,
		OperationsNotCompleteError):
		frappe.db.rollback()
