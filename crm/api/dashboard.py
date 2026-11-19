import json

import frappe
from frappe import _
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Avg, Coalesce, Count, Date, DateFormat, IfNull, Sum
from pypika.functions import Function

from crm.fcrm.doctype.crm_dashboard.crm_dashboard import create_default_manager_dashboard
from crm.utils import sales_user_only


# Custom function for TIMESTAMPDIFF (MySQL/MariaDB)
class TimestampDiff(Function):
	def __init__(self, unit, start, end, **kwargs):
		super().__init__("TIMESTAMPDIFF", unit, start, end, **kwargs)


@frappe.whitelist()
def reset_to_default():
	frappe.only_for("System Manager", True)
	create_default_manager_dashboard(force=True)


@frappe.whitelist()
@sales_user_only
def get_dashboard(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get the dashboard data for the CRM dashboard.
	"""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	roles = frappe.get_roles(frappe.session.user)
	is_sales_manager = "Sales Manager" in roles or "System Manager" in roles
	is_sales_user = "Sales User" in roles and not is_sales_manager

	if is_sales_user:
		user = frappe.session.user

	dashboard = frappe.db.exists("CRM Dashboard", "Manager Dashboard")

	layout = []

	if not dashboard:
		layout = json.loads(create_default_manager_dashboard())
		frappe.db.commit()
	else:
		layout = json.loads(frappe.db.get_value("CRM Dashboard", "Manager Dashboard", "layout") or "[]")

	for l in layout:
		if l.get("name") in ("total_leads", "no_of_prospects"):
			l["tooltip"] = _("Total number of prospects")
		elif l.get("name") in ("average_time_to_close_a_lead", "average_time_to_close_a_prospect"):
			l["tooltip"] = _("Average time taken to close a prospect")
		elif l.get("name") in ("leads_by_source", "prospects_by_source"):
			l["tooltip"] = _("Prospects by source")

		method = globals().get(f"get_{l['name']}")
		if callable(method):
			l["data"] = method(from_date, to_date, user)
		else:
			l["data"] = None

	return layout


@frappe.whitelist()
@sales_user_only
def get_chart(
	name: str, type: str, from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get number chart data for the dashboard.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	roles = frappe.get_roles(frappe.session.user)
	is_sales_manager = "Sales Manager" in roles or "System Manager" in roles
	is_sales_user = "Sales User" in roles and not is_sales_manager

	if is_sales_user:
		user = frappe.session.user

	method = globals().get(f"get_{name}")
	if callable(method):
		return method(from_date, to_date, user)
	else:
		return {"error": _("Invalid chart name")}


def get_total_leads(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get prospect count for the dashboard.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)

	user_cond = ""
	if user:
		from crm.api.security import get_contact_permission_conditions

		perm_cond = get_contact_permission_conditions(user)
		if perm_cond:
			user_cond = f" AND ({perm_cond})"

	query = f"""
		SELECT
			COUNT(DISTINCT CASE WHEN creation >= %(from_date)s AND creation < %(to_date_plus_one)s THEN name ELSE NULL END) as current_month_prospects,
			COUNT(DISTINCT CASE WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s THEN name ELSE NULL END) as prev_month_prospects
		FROM `tabContact`
		WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
		{user_cond}
	"""
	result = frappe.db.sql(
		query,
		{
			"from_date": from_date,
			"to_date_plus_one": to_date_plus_one,
			"prev_from_date": prev_from_date,
		},
		as_dict=True,
	)

	current_month_prospects = (result[0].current_month_prospects if result else 0) or 0
	prev_month_prospects = (result[0].prev_month_prospects if result else 0) or 0

	delta_in_percentage = (
		(current_month_prospects - prev_month_prospects) / prev_month_prospects * 100
		if prev_month_prospects
		else 0
	)

	return {
		"title": _("No. of Prospects"),
		"tooltip": _("Total number of prospects"),
		"value": current_month_prospects,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
	}


get_no_of_prospects = get_total_leads


def get_ongoing_deals(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get ongoing deal count for the dashboard, and also calculate average deal value for ongoing deals.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")

	# Build conditions for current period
	current_cond = (
		(Deal.creation >= from_date)
		& (Deal.creation < to_date_plus_one)
		& (Status.type.notin(["Won", "Lost"]))
	)
	if user:
		current_cond = current_cond & (Deal.deal_owner == user)

	# Build conditions for previous period
	prev_cond = (
		(Deal.creation >= prev_from_date) & (Deal.creation < from_date) & (Status.type.notin(["Won", "Lost"]))
	)
	if user:
		prev_cond = prev_cond & (Deal.deal_owner == user)

	# Build query with CASE expressions
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(
			Count(Case().when(current_cond, Deal.name).else_(None)).as_("current_month_deals"),
			Count(Case().when(prev_cond, Deal.name).else_(None)).as_("prev_month_deals"),
		)
	)

	result = query.run(as_dict=True)

	current_month_deals = result[0].current_month_deals or 0
	prev_month_deals = result[0].prev_month_deals or 0

	delta_in_percentage = (
		(current_month_deals - prev_month_deals) / prev_month_deals * 100 if prev_month_deals else 0
	)

	return {
		"title": _("Ongoing deals"),
		"tooltip": _("Total number of non won/lost deals"),
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
	}


def get_average_ongoing_deal_value(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get ongoing deal count for the dashboard, and also calculate average deal value for ongoing deals.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")

	# Build conditions for current period
	current_cond = (
		(Deal.creation >= from_date)
		& (Deal.creation < to_date_plus_one)
		& (Status.type.notin(["Won", "Lost"]))
	)
	if user:
		current_cond = current_cond & (Deal.deal_owner == user)

	# Build conditions for previous period
	prev_cond = (
		(Deal.creation >= prev_from_date) & (Deal.creation < from_date) & (Status.type.notin(["Won", "Lost"]))
	)
	if user:
		prev_cond = prev_cond & (Deal.deal_owner == user)

	# Calculate deal value with exchange rate
	deal_value_expr = Deal.deal_value * IfNull(Deal.exchange_rate, 1)

	# Build query with CASE expressions
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(
			Avg(Case().when(current_cond, deal_value_expr).else_(None)).as_("current_month_avg_value"),
			Avg(Case().when(prev_cond, deal_value_expr).else_(None)).as_("prev_month_avg_value"),
		)
	)

	result = query.run(as_dict=True)

	current_month_avg_value = result[0].current_month_avg_value or 0
	prev_month_avg_value = result[0].prev_month_avg_value or 0

	avg_value_delta = current_month_avg_value - prev_month_avg_value if prev_month_avg_value else 0

	return {
		"title": _("Avg. ongoing deal value"),
		"tooltip": _("Average deal value of non won/lost deals"),
		"value": current_month_avg_value,
		"delta": avg_value_delta,
		"prefix": get_base_currency_symbol(),
	}


def get_won_deals(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get won deal count for the dashboard, and also calculate average deal value for won deals.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")

	# Build conditions for current period
	current_cond = (
		(Deal.closed_date >= from_date) & (Deal.closed_date < to_date_plus_one) & (Status.type == "Won")
	)
	if user:
		current_cond = current_cond & (Deal.deal_owner == user)

	# Build conditions for previous period
	prev_cond = (Deal.closed_date >= prev_from_date) & (Deal.closed_date < from_date) & (Status.type == "Won")
	if user:
		prev_cond = prev_cond & (Deal.deal_owner == user)

	# Build query with CASE expressions
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(
			Count(Case().when(current_cond, Deal.name).else_(None)).as_("current_month_deals"),
			Count(Case().when(prev_cond, Deal.name).else_(None)).as_("prev_month_deals"),
		)
	)

	result = query.run(as_dict=True)

	current_month_deals = result[0].current_month_deals or 0
	prev_month_deals = result[0].prev_month_deals or 0

	delta_in_percentage = (
		(current_month_deals - prev_month_deals) / prev_month_deals * 100 if prev_month_deals else 0
	)

	return {
		"title": _("Won deals"),
		"tooltip": _("Total number of won deals based on its closure date"),
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
	}


def get_average_won_deal_value(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get won deal count for the dashboard, and also calculate average deal value for won deals.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")

	# Build conditions for current period
	current_cond = (
		(Deal.closed_date >= from_date) & (Deal.closed_date < to_date_plus_one) & (Status.type == "Won")
	)
	if user:
		current_cond = current_cond & (Deal.deal_owner == user)

	# Build conditions for previous period
	prev_cond = (Deal.closed_date >= prev_from_date) & (Deal.closed_date < from_date) & (Status.type == "Won")
	if user:
		prev_cond = prev_cond & (Deal.deal_owner == user)

	# Calculate deal value with exchange rate
	deal_value_expr = Deal.deal_value * IfNull(Deal.exchange_rate, 1)

	# Build query with CASE expressions
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(
			Avg(Case().when(current_cond, deal_value_expr).else_(None)).as_("current_month_avg_value"),
			Avg(Case().when(prev_cond, deal_value_expr).else_(None)).as_("prev_month_avg_value"),
		)
	)

	result = query.run(as_dict=True)

	current_month_avg_value = result[0].current_month_avg_value or 0
	prev_month_avg_value = result[0].prev_month_avg_value or 0

	avg_value_delta = current_month_avg_value - prev_month_avg_value if prev_month_avg_value else 0

	return {
		"title": _("Avg. won deal value"),
		"tooltip": _("Average deal value of won deals"),
		"value": current_month_avg_value,
		"delta": avg_value_delta,
		"prefix": get_base_currency_symbol(),
	}


def get_average_deal_value(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get average deal value for the dashboard.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")

	# Build conditions for current period
	current_cond = (Deal.creation >= from_date) & (Deal.creation < to_date_plus_one) & (Status.type != "Lost")
	if user:
		current_cond = current_cond & (Deal.deal_owner == user)

	# Build conditions for previous period
	prev_cond = (Deal.creation >= prev_from_date) & (Deal.creation < from_date) & (Status.type != "Lost")
	if user:
		prev_cond = prev_cond & (Deal.deal_owner == user)

	# Calculate deal value with exchange rate
	deal_value_expr = Deal.deal_value * IfNull(Deal.exchange_rate, 1)

	# Build query with CASE expressions
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(
			Avg(Case().when(current_cond, deal_value_expr).else_(None)).as_("current_month_avg"),
			Avg(Case().when(prev_cond, deal_value_expr).else_(None)).as_("prev_month_avg"),
		)
	)

	result = query.run(as_dict=True)

	current_month_avg = result[0].current_month_avg or 0
	prev_month_avg = result[0].prev_month_avg or 0

	delta = current_month_avg - prev_month_avg if prev_month_avg else 0

	return {
		"title": _("Avg. deal value"),
		"tooltip": _("Average deal value of ongoing & won deals"),
		"value": current_month_avg,
		"prefix": get_base_currency_symbol(),
		"delta": delta,
		"deltaSuffix": "%",
	}


def get_average_time_to_close_a_lead(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get average time to close a prospect for the dashboard.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	prev_to_date = from_date

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")
	Lead = DocType("CRM Lead")
	Contact = DocType("Contact")

	# Base condition: closed_date is not null and status type is Won
	base_cond = (Deal.closed_date.isnotnull()) & (Status.type == "Won")
	if user:
		base_cond = base_cond & (Deal.deal_owner == user)

	# Current period condition
	current_cond = (Deal.closed_date >= from_date) & (Deal.closed_date < to_date_plus_one)

	# Previous period condition
	prev_cond = (Deal.closed_date >= prev_from_date) & (Deal.closed_date < prev_to_date)

	# Calculate time difference from prospect/deal creation to deal closure
	time_diff = TimestampDiff(
		frappe.qb.terms.LiteralValue("DAY"),
		Coalesce(Contact.creation, Lead.creation, Deal.creation),
		Deal.closed_date,
	)

	# Build query
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.left_join(Contact)
		.on(Deal.contact == Contact.name)
		.left_join(Lead)
		.on(Deal.lead == Lead.name)
		.where(base_cond)
		.select(
			Avg(Case().when(current_cond, time_diff).else_(None)).as_("current_avg_lead"),
			Avg(Case().when(prev_cond, time_diff).else_(None)).as_("prev_avg_lead"),
		)
	)

	result = query.run(as_dict=True)

	current_avg_lead = result[0].current_avg_lead or 0
	prev_avg_lead = result[0].prev_avg_lead or 0
	delta_lead = current_avg_lead - prev_avg_lead if prev_avg_lead else 0

	return {
		"title": _("Avg. time to close a prospect"),
		"tooltip": _("Average time taken from prospect creation to deal closure"),
		"value": current_avg_lead,
		"suffix": " days",
		"delta": delta_lead,
		"deltaSuffix": " days",
		"negativeIsBetter": True,
	}


get_average_time_to_close_a_prospect = get_average_time_to_close_a_lead


def get_average_time_to_close_a_deal(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get average time to close deals for the dashboard.
	"""
	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	to_date_plus_one = frappe.utils.add_days(to_date, 1)
	prev_to_date = from_date

	Deal = DocType("CRM Deal")
	Status = DocType("CRM Deal Status")
	Lead = DocType("CRM Lead")

	# Base condition: closed_date is not null and status type is Won
	base_cond = (Deal.closed_date.isnotnull()) & (Status.type == "Won")
	if user:
		base_cond = base_cond & (Deal.deal_owner == user)

	# Current period condition
	current_cond = (Deal.closed_date >= from_date) & (Deal.closed_date < to_date_plus_one)

	# Previous period condition
	prev_cond = (Deal.closed_date >= prev_from_date) & (Deal.closed_date < prev_to_date)

	# Calculate time difference from deal creation to deal closure
	time_diff = TimestampDiff(frappe.qb.terms.LiteralValue("DAY"), Deal.creation, Deal.closed_date)

	# Build query
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.left_join(Lead)
		.on(Deal.lead == Lead.name)
		.where(base_cond)
		.select(
			Avg(Case().when(current_cond, time_diff).else_(None)).as_("current_avg_deal"),
			Avg(Case().when(prev_cond, time_diff).else_(None)).as_("prev_avg_deal"),
		)
	)

	result = query.run(as_dict=True)

	current_avg_deal = result[0].current_avg_deal or 0
	prev_avg_deal = result[0].prev_avg_deal or 0
	delta_deal = current_avg_deal - prev_avg_deal if prev_avg_deal else 0

	return {
		"title": _("Avg. time to close a deal"),
		"tooltip": _("Average time taken from deal creation to deal closure"),
		"value": current_avg_deal,
		"suffix": " days",
		"delta": delta_deal,
		"deltaSuffix": " days",
		"negativeIsBetter": True,
	}


def get_sales_trend(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get sales trend data for the dashboard.
	[
		{ date: '2024-05-01', prospects: 45, leads: 45, deals: 23, won_deals: 12 },
		{ date: '2024-05-02', prospects: 50, leads: 50, deals: 30, won_deals: 15 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	contact_user_cond = ""
	deal_user_cond = ""
	params = {"from_date": from_date, "to_date": to_date}

	if user:
		from crm.api.security import get_contact_permission_conditions

		perm_cond = get_contact_permission_conditions(user)
		if perm_cond:
			contact_user_cond = f" AND ({perm_cond})"
		deal_user_cond = " AND d.deal_owner = %(user)s"
		params["user"] = user

	query = f"""
		SELECT
			DATE_FORMAT(u.date, '%%Y-%%m-%%d') as date,
			SUM(u.prospects) as prospects,
			SUM(u.deals) as deals,
			SUM(u.won_deals) as won_deals
		FROM (
			SELECT
				DATE(creation) as date,
				COUNT(DISTINCT name) as prospects,
				0 as deals,
				0 as won_deals
			FROM `tabContact`
			WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
			  AND (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  {contact_user_cond}
			GROUP BY DATE(creation)

			UNION ALL

			SELECT
				DATE(d.creation) as date,
				0 as prospects,
				COUNT(*) as deals,
				SUM(CASE WHEN s.type = 'Won' THEN 1 ELSE 0 END) as won_deals
			FROM `tabCRM Deal` d
			JOIN `tabCRM Deal Status` s ON d.status = s.name
			WHERE DATE(d.creation) BETWEEN %(from_date)s AND %(to_date)s
			  {deal_user_cond}
			GROUP BY DATE(d.creation)
		) u
		GROUP BY u.date
		ORDER BY u.date
	"""
	result = frappe.db.sql(query, params, as_dict=True)

	sales_trend = [
		{
			"date": frappe.utils.get_datetime(row.date).strftime("%Y-%m-%d"),
			"prospects": row.prospects or 0,
			"leads": row.prospects or 0,
			"deals": row.deals or 0,
			"won_deals": row.won_deals or 0,
		}
		for row in result
	]

	return {
		"data": sales_trend,
		"title": _("Sales trend"),
		"subtitle": _("Daily performance of prospects, deals, and wins"),
		"xAxis": {
			"title": _("Date"),
			"key": "date",
			"type": "time",
			"timeGrain": "day",
		},
		"yAxis": {
			"title": _("Count"),
		},
		"series": [
			{"name": "prospects", "type": "line", "showDataPoints": True},
			{"name": "deals", "type": "line", "showDataPoints": True},
			{"name": "won_deals", "type": "line", "showDataPoints": True},
		],
	}


def get_forecasted_revenue(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get forecasted revenue for the dashboard.
	[
		{ date: new Date('2024-05-01'), forecasted: 1200000, actual: 980000 },
		{ date: new Date('2024-06-01'), forecasted: 1350000, actual: 1120000 },
		{ date: new Date('2024-07-01'), forecasted: 1600000, actual: "" },
		{ date: new Date('2024-08-01'), forecasted: 1500000, actual: "" },
		...
	]
	"""
	# Using Frappe Query Builder with CASE expressions
	CRMDeal = DocType("CRM Deal")
	CRMDealStatus = DocType("CRM Deal Status")

	# Calculate the date 12 months ago
	twelve_months_ago = frappe.utils.add_months(frappe.utils.nowdate(), -12)

	forecasted_value = (
		Case()
		.when(CRMDealStatus.type == "Lost", CRMDeal.expected_deal_value * IfNull(CRMDeal.exchange_rate, 1))
		.else_(
			CRMDeal.expected_deal_value
			* IfNull(CRMDeal.probability, 0)
			/ 100
			* IfNull(CRMDeal.exchange_rate, 1)
		)
	)

	actual_value = (
		Case()
		.when(CRMDealStatus.type == "Won", CRMDeal.deal_value * IfNull(CRMDeal.exchange_rate, 1))
		.else_(0)
	)

	query = (
		frappe.qb.from_(CRMDeal)
		.join(CRMDealStatus)
		.on(CRMDeal.status == CRMDealStatus.name)
		.select(
			DateFormat(CRMDeal.expected_closure_date, "%Y-%m").as_("month"),
			Sum(forecasted_value).as_("forecasted"),
			Sum(actual_value).as_("actual"),
		)
		.where(CRMDeal.expected_closure_date >= twelve_months_ago)
		.groupby(DateFormat(CRMDeal.expected_closure_date, "%Y-%m"))
		.orderby(DateFormat(CRMDeal.expected_closure_date, "%Y-%m"))
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	for row in result:
		row["month"] = frappe.utils.get_datetime(row["month"]).strftime("%Y-%m-01")
		row["forecasted"] = row["forecasted"] or ""
		row["actual"] = row["actual"] or ""

	return {
		"data": result or [],
		"title": _("Forecasted revenue"),
		"subtitle": _("Projected vs actual revenue based on deal probability"),
		"xAxis": {
			"title": _("Month"),
			"key": "month",
			"type": "time",
			"timeGrain": "month",
		},
		"yAxis": {
			"title": _("Revenue") + f" ({get_base_currency_symbol()})",
		},
		"series": [
			{"name": "forecasted", "type": "line", "showDataPoints": True},
			{"name": "actual", "type": "line", "showDataPoints": True},
		],
	}


def get_funnel_conversion(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get funnel conversion data for the dashboard.
	[
		{ stage: 'Prospects', count: 120 },
		{ stage: 'Qualification', count: 100 },
		{ stage: 'Negotiation', count: 80 },
		{ stage: 'Ready to Close', count: 60 },
		{ stage: 'Won', count: 30 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	contact_user_cond = ""
	deal_conds = ""
	deal_filters = {"from": from_date, "to": to_date}
	params = {"from_date": from_date, "to_date": to_date}

	if user:
		from crm.api.security import get_contact_permission_conditions

		perm_cond = get_contact_permission_conditions(user)
		if perm_cond:
			contact_user_cond = f" AND ({perm_cond})"
		deal_conds += " AND deal_owner = %(user)s"
		deal_filters["user"] = user

	result = []

	# Get total prospects using Contact table
	prospect_query = f"""
		SELECT COUNT(DISTINCT name) as count
		FROM `tabContact`
		WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
		  AND (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
		  {contact_user_cond}
	"""
	total_prospects = frappe.db.sql(prospect_query, params, as_dict=True)
	total_prospects_count = total_prospects[0].count if total_prospects else 0

	result.append({"stage": _("Prospects"), "count": total_prospects_count})

	result += get_deal_status_change_counts(from_date, to_date, deal_conds, deal_filters)

	return {
		"data": result or [],
		"title": _("Funnel conversion"),
		"subtitle": _("Prospect to deal conversion pipeline"),
		"xAxis": {
			"title": _("Stage"),
			"key": "stage",
			"type": "category",
		},
		"yAxis": {
			"title": _("Count"),
		},
		"swapXY": True,
		"series": [
			{
				"name": "count",
				"type": "bar",
				"echartOptions": {
					"colorBy": "data",
				},
			},
		],
	}


def get_deals_by_stage_axis(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get deal data by stage for the dashboard.
	[
		{ stage: 'Prospecting', count: 120 },
		{ stage: 'Negotiation', count: 45 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	# Using Frappe Query Builder with NOT IN clause
	CRMDeal = DocType("CRM Deal")
	CRMDealStatus = DocType("CRM Deal Status")

	query = (
		frappe.qb.from_(CRMDeal)
		.join(CRMDealStatus)
		.on(CRMDeal.status == CRMDealStatus.name)
		.select(CRMDeal.status.as_("stage"), Count("*").as_("count"), CRMDealStatus.type.as_("status_type"))
		.where((Date(CRMDeal.creation).between(from_date, to_date)) & (CRMDealStatus.type.notin(["Lost"])))
		.groupby(CRMDeal.status)
		.orderby(Count("*"), order=frappe.qb.desc)
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	return {
		"data": result or [],
		"title": _("Deals by ongoing & won stage"),
		"xAxis": {
			"title": _("Stage"),
			"key": "stage",
			"type": "category",
		},
		"yAxis": {"title": _("Count")},
		"series": [
			{"name": "count", "type": "bar"},
		],
	}


def get_deals_by_stage_donut(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get deal data by stage for the dashboard.
	[
		{ stage: 'Prospecting', count: 120 },
		{ stage: 'Negotiation', count: 45 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	# Using Frappe Query Builder with JOIN
	CRMDeal = DocType("CRM Deal")
	CRMDealStatus = DocType("CRM Deal Status")

	query = (
		frappe.qb.from_(CRMDeal)
		.join(CRMDealStatus)
		.on(CRMDeal.status == CRMDealStatus.name)
		.select(CRMDeal.status.as_("stage"), Count("*").as_("count"), CRMDealStatus.type.as_("status_type"))
		.where(Date(CRMDeal.creation).between(from_date, to_date))
		.groupby(CRMDeal.status)
		.orderby(Count("*"), order=frappe.qb.desc)
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	return {
		"data": result or [],
		"title": _("Deals by stage"),
		"subtitle": _("Current pipeline distribution"),
		"categoryColumn": "stage",
		"valueColumn": "count",
	}


def get_lost_deal_reasons(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get lost deal reasons for the dashboard.
	[
		{ reason: 'Price too high', count: 20 },
		{ reason: 'Competitor won', count: 15 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	# Using Frappe Query Builder with JOIN
	CRMDeal = DocType("CRM Deal")
	CRMDealStatus = DocType("CRM Deal Status")

	query = (
		frappe.qb.from_(CRMDeal)
		.join(CRMDealStatus)
		.on(CRMDeal.status == CRMDealStatus.name)
		.select(CRMDeal.lost_reason.as_("reason"), Count("*").as_("count"))
		.where((Date(CRMDeal.creation).between(from_date, to_date)) & (CRMDealStatus.type == "Lost"))
		.groupby(CRMDeal.lost_reason)
		.having((CRMDeal.lost_reason.isnotnull()) & (CRMDeal.lost_reason != ""))
		.orderby(Count("*"), order=frappe.qb.desc)
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	return {
		"data": result or [],
		"title": _("Lost deal reasons"),
		"subtitle": _("Common reasons for losing deals"),
		"xAxis": {
			"title": _("Reason"),
			"key": "reason",
			"type": "category",
		},
		"yAxis": {
			"title": _("Count"),
		},
		"series": [
			{"name": "count", "type": "bar"},
		],
	}


def get_leads_by_source(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get prospect data by source for the dashboard.
	Contacts do not currently store a source field, so this returns an empty list without error.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	result = []
	if frappe.db.has_column("Contact", "source"):
		user_cond = ""
		params = {"from_date": from_date, "to_date": to_date}
		if user:
			from crm.api.security import get_contact_permission_conditions

			perm_cond = get_contact_permission_conditions(user)
			if perm_cond:
				user_cond = f" AND ({perm_cond})"

		query = f"""
			SELECT IFNULL(source, 'Empty') as source, COUNT(DISTINCT name) as count
			FROM `tabContact`
			WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
			  AND (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  {user_cond}
			GROUP BY source
			ORDER BY count DESC
		"""
		result = frappe.db.sql(query, params, as_dict=True)

	return {
		"data": result or [],
		"title": _("Prospects by source"),
		"subtitle": _("Prospect generation channel analysis"),
		"categoryColumn": "source",
		"valueColumn": "count",
	}


get_prospects_by_source = get_leads_by_source


def get_deals_by_source(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get deal data by source for the dashboard.
	[
		{ source: 'Website', count: 120 },
		{ source: 'Referral', count: 45 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	# Using Frappe Query Builder
	CRMDeal = DocType("CRM Deal")

	query = (
		frappe.qb.from_(CRMDeal)
		.select(IfNull(CRMDeal.source, "Empty").as_("source"), Count("*").as_("count"))
		.where(Date(CRMDeal.creation).between(from_date, to_date))
		.groupby(CRMDeal.source)
		.orderby(Count("*"), order=frappe.qb.desc)
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	return {
		"data": result or [],
		"title": _("Deals by source"),
		"subtitle": _("Deal generation channel analysis"),
		"categoryColumn": "source",
		"valueColumn": "count",
	}


def get_deals_by_territory(from_date: str | None = None, to_date: str | None = None, user: str | None = None):
	"""
	Get deal data by territory for the dashboard.
	[
		{ territory: 'North America', deals: 45, value: 2300000 },
		{ territory: 'Europe', deals: 30, value: 1500000 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	# Using Frappe Query Builder with complex aggregations
	CRMDeal = DocType("CRM Deal")

	query = (
		frappe.qb.from_(CRMDeal)
		.select(
			IfNull(CRMDeal.territory, "Empty").as_("territory"),
			Count("*").as_("deals"),
			Sum(Coalesce(CRMDeal.deal_value, 0) * IfNull(CRMDeal.exchange_rate, 1)).as_("value"),
		)
		.where(Date(CRMDeal.creation).between(from_date, to_date))
		.groupby(CRMDeal.territory)
		.orderby(Count("*"), order=frappe.qb.desc)
		.orderby(
			Sum(Coalesce(CRMDeal.deal_value, 0) * IfNull(CRMDeal.exchange_rate, 1)), order=frappe.qb.desc
		)
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	return {
		"data": result or [],
		"title": _("Deals by territory"),
		"subtitle": _("Geographic distribution of deals and revenue"),
		"xAxis": {
			"title": _("Territory"),
			"key": "territory",
			"type": "category",
		},
		"yAxis": {
			"title": _("Number of deals"),
		},
		"y2Axis": {
			"title": _("Deal value") + f" ({get_base_currency_symbol()})",
		},
		"series": [
			{"name": "deals", "type": "bar"},
			{"name": "value", "type": "line", "showDataPoints": True, "axis": "y2"},
		],
	}


def get_deals_by_salesperson(
	from_date: str | None = None, to_date: str | None = None, user: str | None = None
):
	"""
	Get deal data by salesperson for the dashboard.
	[
		{ salesperson: 'John Smith', deals: 45, value: 2300000 },
		{ salesperson: 'Jane Doe', deals: 30, value: 1500000 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	# Using Frappe Query Builder with LEFT JOIN
	CRMDeal = DocType("CRM Deal")
	User = DocType("User")

	query = (
		frappe.qb.from_(CRMDeal)
		.left_join(User)
		.on(User.name == CRMDeal.deal_owner)
		.select(
			IfNull(User.full_name, CRMDeal.deal_owner).as_("salesperson"),
			Count("*").as_("deals"),
			Sum(Coalesce(CRMDeal.deal_value, 0) * IfNull(CRMDeal.exchange_rate, 1)).as_("value"),
		)
		.where(Date(CRMDeal.creation).between(from_date, to_date))
		.groupby(CRMDeal.deal_owner)
		.orderby(Count("*"), order=frappe.qb.desc)
		.orderby(
			Sum(Coalesce(CRMDeal.deal_value, 0) * IfNull(CRMDeal.exchange_rate, 1)), order=frappe.qb.desc
		)
	)

	if user:
		query = query.where(CRMDeal.deal_owner == user)

	result = query.run(as_dict=True)

	return {
		"data": result or [],
		"title": _("Deals by salesperson"),
		"subtitle": _("Number of deals and total value per salesperson"),
		"xAxis": {
			"title": _("Salesperson"),
			"key": "salesperson",
			"type": "category",
		},
		"yAxis": {
			"title": _("Number of deals"),
		},
		"y2Axis": {
			"title": _("Deal value") + f" ({get_base_currency_symbol()})",
		},
		"series": [
			{"name": "deals", "type": "bar"},
			{"name": "value", "type": "line", "showDataPoints": True, "axis": "y2"},
		],
	}


def get_base_currency_symbol():
	"""
	Get the base currency symbol from the system settings.
	"""
	base_currency = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
	return frappe.db.get_value("Currency", base_currency, "symbol") or ""


def get_deal_status_change_counts(
	from_date: str | None = None,
	to_date: str | None = None,
	deal_conds: str = "",
	filters: dict | None = None,
):
	"""
	Get count of each status change (to) for each deal, excluding deals with current status type 'Lost'.
	Order results by status position.
	Returns:
	[
	  {"status": "Qualification", "count": 120},
	  {"status": "Negotiation", "count": 85},
	  ...
	]
	"""
	# Using Frappe Query Builder with multiple JOINs and table aliases
	CRMStatusChangeLog = DocType("CRM Status Change Log")
	CRMDeal = DocType("CRM Deal")
	CurrentStatus = DocType("CRM Deal Status").as_("s")
	TargetStatus = DocType("CRM Deal Status").as_("st")

	query = (
		frappe.qb.from_(CRMStatusChangeLog)
		.join(CRMDeal)
		.on(CRMStatusChangeLog.parent == CRMDeal.name)
		.join(CurrentStatus)
		.on(CRMDeal.status == CurrentStatus.name)
		.join(TargetStatus)
		.on(CRMStatusChangeLog.to == TargetStatus.name)
		.select(CRMStatusChangeLog.to.as_("stage"), Count("*").as_("count"))
		.where(
			(CRMStatusChangeLog.to.isnotnull())
			& (CRMStatusChangeLog.to != "")
			& (CurrentStatus.type != "Lost")
			& (Date(CRMDeal.creation).between(from_date, to_date))
		)
		.groupby(CRMStatusChangeLog.to, TargetStatus.position)
		.orderby(TargetStatus.position)
	)

	# Handle optional user filter if deal_conds contains user condition
	if filters and filters.get("user"):
		query = query.where(CRMDeal.deal_owner == filters["user"])

	result = query.run(as_dict=True)
	return result or []
