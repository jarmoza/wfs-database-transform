#!/usr/bin/env python
# coding=utf-8

""" Module for the Conversion of Bridget Moynihan's JSON for Edwin Morgan's Scrapbooks

This script converts from one db JSON format to another for the book/page level
prototype of "Working from Scraps", a project that navigates and exposes examples of metadata 
from Edwin Morgan's scrapbooks.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

"""

__author__ = "Jonathan Armoza"
__contact__ = "jarmoza@gmail.com"
__copyright__ = "Copyright 2019, Jonathan Armoza"
__credits__ = ["Jonathan Armoza", "Bridget Moynihan"]
__date__ = "2019/09/03"
__deprecated__ = False
__license__ = "GPLv3"
__maintainer__ = "developer"
__status__ = "Production"
__version__ = "1.0.8"


from collections import Counter
import decimal
import json
import os
import re
import string


# Quickly transform string month to number
month_dict = {
    "January"   : 1,
    "February"  : 2,
    "March"     : 3,
    "April"     : 4,
    "May"       : 5,
    "June"      : 6,
    "July"      : 7,
    "August"    : 8,
    "September" : 9, 
    "October"   : 10,
    "November"  : 11,
    "December"  : 12
}

# Regex for format description
desc_regex = re.compile(r"\|\s*[A-Za-z\s]+\s*\[\d+\]\s*\|", re.IGNORECASE)

def anchor_routes_from_formatted_text_old(p_formatted_line, p_route):

	# |Name [id]| - yields anchor tag to this person page

	substitutions = re.findall(desc_regex, p_formatted_line)
	# print "Substitutions: {0}".format(substitutions)
	line_with_tags = p_formatted_line

	for index in range(len(substitutions)):

		# print "Sub[{0}]: {1}".format(index, substitutions[index])

		parts = substitutions[index].strip().strip("|").split("[")

		for index2 in range(len(parts)):
			parts[index2] = parts[index2].strip().strip("]")

		anchor_tag = "<a href='{0}/{1}'>{2}</a>".format(p_route, parts[1], parts[0])

		line_with_tags = line_with_tags.replace(substitutions[index], anchor_tag) 

		# print "line_with_tags: {0}".format(line_with_tags)

	return line_with_tags

def anchor_routes_from_formatted_text(p_formatted_line, p_route):

	line_with_tags = p_formatted_line

	# 1. Find all indices of "|" special characters
	pipe_instances = []
	for index in range(len(p_formatted_line)):
		if "|" == p_formatted_line[index]:
			pipe_instances.append(index)
	if len(pipe_instances) % 2 == 1:
		print line_with_tags

	# 2. Parse out the person name and ID and replace them with an anchor tag
	for index in xrange(0, len(pipe_instances), 2):

		# Two pipes surround a person tag
		person_tag = p_formatted_line[pipe_instances[index]:pipe_instances[index + 1] + 1]

		# Strip whitespace and pipes, get for ID
		parts = person_tag.strip().strip("|").split("[")
		for index2 in range(len(parts)):
			parts[index2] = parts[index2].strip().strip("]")

		if len(parts) < 2:
			print parts

		# Anchor tag for person
		anchor_tag = "<a href='{0}/{1}'>{2}</a>".format(p_route, parts[1], parts[0].encode("utf-8"))

		# Replace piped person tag with formatted anchor tag
		line_with_tags = line_with_tags.replace(person_tag, anchor_tag.decode('utf-8'))

	return line_with_tags	

def format_description(p_str_description):

	# NOTE: Gathered (in post) by searching json descriptions for endline possiblities
	endline_list = [u'%\n\n\n', u'%', u'%\n\n', u'%\n', u'%\n\r\n',
					u'%\n\n\r\n', u'%\r\n', u'\r\n\r\n', u'%\r\n\r\n',
					u'\n\n\n', u'\n\n', u'%\r\n\r\n\r\n', u'\r\n']

	# Split out the description into separate lines
	formatted_description = p_str_description
	for endline in endline_list:
		formatted_description = formatted_description.replace(endline, "<br/>")
	paragraphs = formatted_description.split("<br/>")

	# (1) Italicize/bold the phrases "Identified Clippings:" and "Unidentified Clippings:"
	# (2) Replace ID'd persons with anchor tags to route to their page
	# (3) Turn each line into a paragraph tag
	for index in range(len(paragraphs)):

		paragraphs[index] = style_text(paragraphs[index], "Identified Clippings:", "italic")
		paragraphs[index] = weight_text(paragraphs[index], "Identified Clippings:", "bold")

		paragraphs[index] = style_text(paragraphs[index], "Unidentified Clippings:", "italic")
		paragraphs[index] = weight_text(paragraphs[index], "Unidentified Clippings:", "bold")

		paragraphs[index] = anchor_routes_from_formatted_text(paragraphs[index], "/collection/person")
		paragraphs[index] = "<p class=\"desc_paragraph\">" + paragraphs[index].strip().strip("%").strip() + "</p>"

	return "".join(paragraphs).strip()

def get_month_number(p_month_str):
	
	return month_dict[p_month_str] if p_month_str in month_dict else "N/A"

def get_obj_from_dd_month_year(p_date_string):

	date_parts = p_date_string.strip().split(" ")
	date_obj = {}
	# if 3 == len(date_parts):
	# 	date_obj = { "day": int(date_parts[0]),
	#          		 "month": month_dict[date_parts[1]],
	#          		 "year": int(date_parts[2]) }

	# length(1)
	# [u'']
	# [u'1882']
	# [u'c.1270']
	# [u'c.1430/1440']
	# [u'683?']
	# [u'1140s']
	# [u'c1181']
	# [u'?']

	# length(2)
	# [u'November', u'1606']
	# [u'c.99', u'BC']
	# [u'627', u'BC']
	# [u'4', u'BC?']
	# [u'30/33', u'BC?']
	# [u'36-39', u'AD']
	# [u'61', u'AD']
	# [u'c.113', u'AD']
	# [u'c.', u'1395']
	# [u'c.1350', u'BCE']
	# [u'fl.', u'1596']
	# [u'c', u'1850-1859']
	# [u'after', u'1923']
	# [u'c.', u'1525-1530']

	# length(3)
	# [u'3', u'December', u'1919']
	# [u'bap.25', u'July', u'1556']
	# [u'c.9', u'November', u'1596']
	# [u'reign', u'668', u'BC']
	# [u'c.', u'460', u'BC']
	# [u'fl.', u'1971', u'BC']
	# [u'c', u'319', u'BC']
	# [u'3rd', u'Century', u'BC']
	# [u'4th', u'Century', u'BC']		

	# > length(3)
	# [u'fl.', u'4', u'Century', u'BC?']
	# [u'27', u'November', u'8', u'BC']
	# [u'bap', u'11', u'July', u'1558']
	# [u'bap.', u'26', u'February', u'1564']
	# [u'fl.', u'1st', u'and', u'2nd', u'century', u'AD']

	# if len(date_parts) == 3:
	# 	try:
	# 		if not (int(date_parts[0]) >= 1 and int(date_parts[0]) <= 31 and
	# 		   "N/A" != get_month_number(date_parts[1]) and 
	# 		   int(date_parts[2]) >= 0 and int(date_parts[2]) <= 2018):
	# 			print date_parts		     
	# 	except:
	# 		print date_parts

	return date_obj

def has_number(p_string):

	return any(char.isdigit() for char in p_string)

def update_stat(p_value_to_check, p_stat_dict):

	if len(p_value_to_check.strip()) > 0:
		if p_value_to_check not in p_stat_dict:
			p_stat_dict[p_value_to_check] = 1
		else:
			p_stat_dict[p_value_to_check] += 1

def style_text(p_text, p_substring, p_font_style):

	new_span = "<span style=\"font-style: " + p_font_style + ";\">" + p_substring + "</span>"
	return string.replace(p_text, p_substring, new_span)

def weight_text(p_text, p_substring, p_weight):

	new_span = "<span style=\"font-weight: " + p_weight + ";\">" + p_substring + "</span>"
	return string.replace(p_text, p_substring, new_span)	

# Helper functions for people, places, sources, and keywords
def find_associated_pps_helper(p_pps, p_page, p_pps_ids_str, p_pps_on_pages_dict_str):	

	# Save all people associated with this page
	p_pps["stats"][p_pps_ids_str].extend(p_page[p_pps_ids_str])

	# Note these pps are on this page that this pps is also on
	for pps_id in p_page[p_pps_ids_str]:
		if pps_id not in p_pps["stats"][p_pps_on_pages_dict_str]:
			p_pps["stats"][p_pps_on_pages_dict_str][pps_id] = []
		p_pps["stats"][p_pps_on_pages_dict_str][pps_id].append(p_page["id"])		

def find_associated_pps(p_pps_collection, p_pages, p_pps_ids_str):

	# Note people, places, and sources found on pages with this pps's in this collection
	for pps in p_pps_collection:

		for page in p_pages.m_pages:

			# If this pps is on this page
			if pps["id"] in page[p_pps_ids_str]:

				# Save all pps associated with this page and,
				# Note these people are on this page that this source is also on
				find_associated_pps_helper(pps, page, "people_ids", "people_on_pages_dict")
				find_associated_pps_helper(pps, page, "places_ids", "places_on_pages_dict")
				find_associated_pps_helper(pps, page, "sources_ids", "sources_on_pages_dict")

		# De-duplicate the people, places, and sources ID lists
		pps["stats"]["people_ids"] = list(set(pps["stats"]["people_ids"]))			
		pps["stats"]["places_ids"] = list(set(pps["stats"]["places_ids"]))
		pps["stats"]["sources_ids"] = list(set(pps["stats"]["sources_ids"]))

		# Remove the pps' own ID from the pps type list it would belong to
		if pps["id"] in pps["stats"][p_pps_ids_str]:
			pps["stats"][p_pps_ids_str].remove(pps["id"])		

def find_associated_keywords(p_pps_collection, p_pages, p_pps_ids_str):

	# Add keywords from pages that each pps is on
	for pps in p_pps_collection:
		for page in p_pages.m_pages:
			if pps["id"] in page[p_pps_ids_str]:
				pps["stats"]["keywords_ids"].extend(page["keywords"])
				pps["stats"]["ukat_keywords_ids"].extend(page["ukat_keywords"])



class WfsScrapBooks:

	def __init__(self, p_book_json_filename):

		self.m_book_json_filename = p_book_json_filename
		self.m_collection = { "stats": {} }
		self.m_books = [];
		self.ingest()

	def debug_output(self):

		for book in self.m_books:
			print "\n============================"
			print "Scrapbook {0}".format(book["number"])
			print book

	def debug_stats(self):

		for book in self.m_books:
			print "\n============================"
			print "Scrapbook {0}".format(book["number"])
			for key in book["stats"]:
				print "{0}: {1}".format(key, book["stats"][key])

	def ingest(self):

		with open(self.m_book_json_filename, "rU") as input_file:

			# Read the JSON
			book_json = json.loads(input_file.read())

			# Save each book entry
			for entry in book_json["RECORDS"]:
				self.save_book(entry)

			# Sort the books by collection number
			self.m_books = sorted(self.m_books, key=lambda x: int(x["number"]), reverse=False)

	def output(self, p_pages, p_output_path):

		# 1. Output stats for collection overview
		output_filename = "wfs_collection_overview.json"
		output_json = self.m_collection["stats"]
		with open(p_output_path + output_filename, "w") as output_file:
			output_file.write(json.dumps(output_json))

		# 2. Output stats for each book
		for book in self.m_books:

			# Filename per book w/ name format wfs_<id>_scrapbook<number>.json
			output_filename = "wfs_scrapbook_{0:02d}.json".format(int(book["number"]))

			# JSON will include book data and pages data
			output_json = { "book": book, "pages": p_pages.m_pages_by_book_dict[book["id"]] }

			# Output the combined book and pages data
			with open(p_output_path + output_filename, "w") as output_file:
				output_file.write(json.dumps(output_json))

	def save_book(self, p_json_entry):

		# "Scrapbook_Id":"1",
		# "Scrapbook_number":"1",
		# "Scrapbook_pg_range":"215c-403b",
		# "Scrapbook_date_range":"1931-1953",
		# "Scrapbook_height_cm":"32",
		# "Scrapbook_width_cm":"20",
		# "Scrapbook_depth_cm":"4",
		# "Scrapbook_cover_image":"y",
		# "Scrapbook_materiality_desc":"Course, engrained navy blue cover with burgundy binding. Binding has a faux leather pattern on it, pages are bound in groups and have mottled edges. There is a black and white image of a lake and mountains pasted onto the front cover. Possibly the Highlan",
		# "Scrapbook_notes":"Morgan notes the material for this book were collected in 1937. Morgan also notes \"1931 AD = the year 1 FS\"",
		# "Scrapbook_cover_image_ids":"MS_MORGAN_C_1_Back Binding; MS_MORGAN_C_1_Front Binding; MS_MORGAN_C_1_Spine",
		# "Scrapbook_tempcover_filename": "./src/assets/book1.png"

		# Pre-format numeric fields in case they are blank in the original input JSON
		begin_date = ""
		end_date = ""
		if has_number(p_json_entry["Scrapbook_date_range"]):
			date_components = p_json_entry["Scrapbook_date_range"].split("-")
			begin_date = int(date_components[0].strip())
			end_date = int(date_components[1].strip())
		height = ""
		if has_number(p_json_entry["Scrapbook_height_cm"]):
			height = float(p_json_entry["Scrapbook_height_cm"])
		width = ""
		if has_number(p_json_entry["Scrapbook_width_cm"]):
			width = float(p_json_entry["Scrapbook_width_cm"])
		depth = ""
		if has_number(p_json_entry["Scrapbook_depth_cm"]):
			depth = float(p_json_entry["Scrapbook_depth_cm"])

		self.m_books.append({

			# Record data
			"id": p_json_entry["Scrapbook_Id"],
			"number": p_json_entry["Scrapbook_number"],
			"pages": p_json_entry["Scrapbook_pg_range"],
			"begin_date": begin_date,
			"end_date": end_date,
			"height": height,
			"width": width,
			"depth": depth,
			"materiality_desc": p_json_entry["Scrapbook_materiality_desc"],
			"notes": p_json_entry["Scrapbook_notes"],
			# "cover_image_filename": p_json_entry["Scrapbook_tempcover_filename"],

			# Stats
			"stats": {

				"pages": 0,
				"pages_foldouts": 0,
				"pages_foldouts_list": [],
				"avg_clipping_per_page": 0,
				"clippings": 0,
				"clippings_w_metadata": 0,
				"keyword_count_dict": {},
				"keyword_to_page_dict": {},				
				"clipping_orientation_to_page_dict": {}, # all horizontal, all vertical, mixed, etc.
				"clipping_orientation_page_counts": {},
				"orig_material_counts": {},
				"pages_w_orig_material_dict": {"Y": [], "N": []},
				"pages_by_date_ranges_dict": {},
				"common_dates_by_pages_dict": {},

				"people_ids": [],
				"places_ids": [],
				"sources_ids": [],
				"people_ids_dict": {},
				"places_ids_dict": {},
				"sources_ids_dict": {},
				
				# Secondary stats
				"role_type_counts": {},
				"roles_by_people_ids": {},
				"continent_counts": {},	
				"source_type_counts": {},

			},
		})

	def save_continent_counts(self):

		# Collection level (book is already processed)
		for book in self.m_books:
			for continent in book["stats"]["continent_counts"]:
				if continent not in self.m_collection["stats"]["continent_counts"]:
					self.m_collection["stats"]["continent_counts"][continent] = 0
				self.m_collection["stats"]["continent_counts"][continent] += book["stats"]["continent_counts"][continent]

	def save_people_roles(self, p_pages):

		# Book level
		role_types = []
		for book in self.m_books:

			for page in p_pages.m_pages:
				if book["id"] == page["book_id"]:
					for person_id in page["people_roles"]:
						if person_id not in book["stats"]["roles_by_people_ids"]:
							book["stats"]["roles_by_people_ids"][person_id] = []
						book["stats"]["roles_by_people_ids"][person_id].extend(page["people_roles"][person_id])			
						role_types.extend(page["people_roles"][person_id])

			role_type_counter = Counter(role_types)
			for key in role_type_counter:
				book["stats"]["role_type_counts"][key] = role_type_counter[key]

		# De-duplicate roles for people
		for person_id in self.m_collection["stats"]["roles_by_people_ids"]:
			self.m_collection["stats"]["roles_by_people_ids"][person_id] = list(set(self.m_collection["stats"]["roles_by_people_ids"][person_id]))		

		# Collection level
		role_types = []
		for page in p_pages.m_pages:
			for person_id in page["people_roles"]:
				if person_id not in self.m_collection["stats"]["roles_by_people_ids"]:
					self.m_collection["stats"]["roles_by_people_ids"][person_id] = []
				self.m_collection["stats"]["roles_by_people_ids"][person_id].extend(page["people_roles"][person_id])
				role_types.extend(page["people_roles"][person_id])
		role_type_counter = Counter(role_types)
		for key in role_type_counter:
			self.m_collection["stats"]["role_type_counts"][key] = role_type_counter[key]

		# De-duplicate roles for people
		for person_id in self.m_collection["stats"]["roles_by_people_ids"]:
			self.m_collection["stats"]["roles_by_people_ids"][person_id] = list(set(self.m_collection["stats"]["roles_by_people_ids"][person_id]))

	def save_source_types(self, p_sources):

		# Book level
		source_types = []
		for book in self.m_books:
			for source_id in book["stats"]["sources_ids_dict"]:
				for index in range(book["stats"]["sources_ids_dict"][source_id]):
					source_types.append(p_sources.m_sources_dict[source_id]["source_type"])
	
			source_type_counter = Counter(source_types)
			for key in source_type_counter:
				book["stats"]["source_type_counts"][key] = source_type_counter[key]

		# Collection level
		source_types = []
		for source in p_sources.m_sources:
			source_types.append(source["source_type"])
		source_type_counter = Counter(source_types)
		for key in source_type_counter:
			self.m_collection["stats"]["source_type_counts"][key] = source_type_counter[key]

	def save_stats(self, p_pages):

		# 1. Tally book stats

		# "pages": 0,
		# "pages_foldouts": 0,
		# "pages_foldouts_list": [],
		# "avg_clipping_per_page": 0,
		# "clippings": 0,
		# "keyword_count_dict",
		# "keyword_to_page_dict": {},				
		# "clipping_orientation_to_page_dict": {}, # all horizontal, all vertical, mixed, etc.
		# "clipping_orientation_page_counts: {},"
		# "orig_material_counts": {},
		# "pages_w_orig_material_dict": {},
		# "pages_by_date_ranges_dict": {},
		# "common_dates_by_pages_dict": {}

		# New
		# "people_ids": [],
		# "places_ids": [],
		# "sources_ids": [],
		# "people_ids_dict": {},
		# "places_ids_dict": {},
		# "sources_ids_dict": {},

		for book in self.m_books:

			clipping_counts = []
			clipping_w_metadata_counts = []
			people_ids = []
			places_ids = []
			sources_ids = []

			for page in p_pages.m_pages_by_book_dict[book["id"]]:

				if book["id"] == page["book_id"]:

					# if "" in page["places_ids"]:
					# 	print "FOUND blank place on page {0} in book {1}".format(page["id"], book["number"])

					# Tally page count	
					book["stats"]["pages"] += 1

					# Tally pages with foldouts and save pages to pages with foldout list
					if "" != page["foldout"] and "Y" == page["foldout"]:
						book["stats"]["pages_foldouts"] += 1
						book["stats"]["pages_foldouts_list"].append(page["id"])

					# Save clipping counts for averaging and tally clippings
					clipping_counts.append(page["clippings"])
					book["stats"]["clippings"] += page["clippings"]

					# Save clipping counts w/metadata for averaging and tally clippings
					clipping_w_metadata_counts.append(page["clippings_w_metadata"])
					book["stats"]["clippings_w_metadata"] += page["clippings_w_metadata"]					

					# Save all keywords and their counts in a dictionary
					for kw in page["keywords"]:
						update_stat(kw, book["stats"]["keyword_count_dict"])

						# Save page to keyword to pages dictionary
						if kw not in book["stats"]["keyword_to_page_dict"]:
							book["stats"]["keyword_to_page_dict"][kw] = []
						book["stats"]["keyword_to_page_dict"][kw].append(page["id"])

					# Update counts for various orientations
					for orientation in page["orientations"]:
						update_stat(orientation, book["stats"]["clipping_orientation_page_counts"])

						# Save page to orientation to pages dictionary
						if orientation not in book["stats"]["clipping_orientation_to_page_dict"]:
							book["stats"]["clipping_orientation_to_page_dict"][orientation] = []
						book["stats"]["clipping_orientation_to_page_dict"][orientation].append(page["id"])

					# Original material
					if "" != page["orig_material"]:
					
						# Tally pages with and without original material
						update_stat(page["orig_material"], book["stats"]["orig_material_counts"])

						# Save the page to the dictionaries for with/without original material
						book["stats"]["pages_w_orig_material_dict"][page["orig_material"]].append(page["id"])
					
					# Add persons, places, sources
					book["stats"]["people_ids"].extend(page["people_ids"])
					book["stats"]["places_ids"].extend(page["places_ids"])
					book["stats"]["sources_ids"].extend(page["sources_ids"])

					# Tally continents
					for continent in page["stats"]["continent_counts"]:
						if continent not in book["stats"]["continent_counts"]:
							book["stats"]["continent_counts"][continent] = 0
						book["stats"]["continent_counts"][continent] += page["stats"]["continent_counts"][continent]

					# NOTE: To be implemented

					# "pages_by_date_ranges_dict": {},
					# date_range = get_date_range(page)
					# update_stat(date_range, book["stats"]["common_dates_by_pages_dict"])

					# "pages_by_date_ranges_dict": {}
					# book["stats"]["pages_by_date_ranges_dict"][date_range].append(page["id"])

			# Calculate and save the average number of clippings per page (rounded to two places)
			book["stats"]["avg_clipping_per_page"] = float(sum(clipping_counts)) / float(len(clipping_counts))
			book["stats"]["avg_clipping_per_page"] = str(round(decimal.Decimal(book["stats"]["avg_clipping_per_page"]), 2))

			# Tally people, place, source counts
			people_counter = Counter(book["stats"]["people_ids"])
			for key in people_counter.keys():
				book["stats"]["people_ids_dict"][key] = people_counter[key]
			places_counter = Counter(book["stats"]["places_ids"])
			for key in places_counter.keys():
				book["stats"]["places_ids_dict"][key] = places_counter[key]
			sources_counter = Counter(book["stats"]["sources_ids"])
			for key in sources_counter.keys():
				book["stats"]["sources_ids_dict"][key] = sources_counter[key]

			# Keep unique people, place, and source IDs
			book["stats"]["people_ids"] = list(set(book["stats"]["people_ids"]))
			book["stats"]["places_ids"] = list(set(book["stats"]["places_ids"]))
			book["stats"]["sources_ids"] = list(set(book["stats"]["sources_ids"]))

		# 2. Tally collection stats
		self.m_collection["stats"]["pages"] = 0
		self.m_collection["stats"]["pages_foldouts"] = 0
		self.m_collection["stats"]["clippings"] = 0
		self.m_collection["stats"]["clippings_w_metadata"] = 0
		self.m_collection["stats"]["avg_clippings_per_book"] = 0
		self.m_collection["stats"]["keyword_count_dict"] = {}
		self.m_collection["stats"]["keyword_to_book_dict"] = {}
		self.m_collection["stats"]["keywords_to_ids"] = {}
		self.m_collection["stats"]["ids_to_keywords"] = {}
		self.m_collection["stats"]["total_date_range"] = []
		self.m_collection["stats"]["people_ids_dict"] = {}
		self.m_collection["stats"]["places_ids_dict"] = {}
		self.m_collection["stats"]["sources_ids_dict"] = {}
		
		self.m_collection["stats"]["source_type_counts"] = {}
		self.m_collection["stats"]["role_type_counts"] = {}
		self.m_collection["stats"]["roles_by_people_ids"] = {}
		self.m_collection["stats"]["continent_counts"] = {}

		for book in self.m_books:

			# Total number of pages
			self.m_collection["stats"]["pages"] += book["stats"]["pages"]

			# Total number of pages with foldouts
			self.m_collection["stats"]["pages_foldouts"] += book["stats"]["pages_foldouts"]

			# Total number of clippings
			self.m_collection["stats"]["clippings"] += book["stats"]["clippings"]

			# Total number of clippings w/ metadata
			self.m_collection["stats"]["clippings_w_metadata"] += book["stats"]["clippings_w_metadata"]

			# Sum for average number of clippings per book
			self.m_collection["stats"]["avg_clippings_per_book"] += book["stats"]["clippings"]

			# Build keyword dict with counts for collection 
			for kw in book["stats"]["keyword_count_dict"]:
				update_stat(kw, self.m_collection["stats"]["keyword_count_dict"])

			# Build keyword to book dict
			for kw in book["stats"]["keyword_count_dict"]:
				if kw not in self.m_collection["stats"]["keyword_to_book_dict"]:
					self.m_collection["stats"]["keyword_to_book_dict"][kw] = []
				self.m_collection["stats"]["keyword_to_book_dict"][kw].append(book["number"])

			# Tally people, places, and sources by ID
			for key in book["stats"]["people_ids_dict"]:
				if key not in self.m_collection["stats"]["people_ids_dict"]:
					self.m_collection["stats"]["people_ids_dict"][key] = 0
				self.m_collection["stats"]["people_ids_dict"][key] += book["stats"]["people_ids_dict"][key]
			for key in book["stats"]["places_ids_dict"]:
				if key not in self.m_collection["stats"]["places_ids_dict"]:
					self.m_collection["stats"]["places_ids_dict"][key] = 0
				self.m_collection["stats"]["places_ids_dict"][key] += book["stats"]["places_ids_dict"][key]
			for key in book["stats"]["sources_ids_dict"]:
				if key not in self.m_collection["stats"]["sources_ids_dict"]:
					self.m_collection["stats"]["sources_ids_dict"][key] = 0
				self.m_collection["stats"]["sources_ids_dict"][key] += book["stats"]["sources_ids_dict"][key]


		# Finish calculation of average number of clippings per book
		self.m_collection["stats"]["avg_clippings_per_book"] /= float(len(self.m_books))
		self.m_collection["stats"]["avg_clippings_per_book"] = str(round(decimal.Decimal(self.m_collection["stats"]["avg_clippings_per_book"]), 2))

		# Create IDs for keywords (for keyword pages/routing)
		keyword_id = 1
		for keyword in self.m_collection["stats"]["keyword_count_dict"]:
			self.m_collection["stats"]["keywords_to_ids"][keyword] = str(keyword_id)
			self.m_collection["stats"]["ids_to_keywords"][str(keyword_id)] = keyword
			keyword_id += 1


class WfsPages:

	def __init__(
		self, 
		p_page_json_filename, 
		p_peoplejoin_json_filename, 
		p_placesjoin_json_filename, 
		p_sourcesjoin_json_filename):

		self.m_page_json_filename = p_page_json_filename
		self.m_peoplejoin_json_filename = p_peoplejoin_json_filename
		self.m_placesjoin_json_filename = p_placesjoin_json_filename
		self.m_sourcesjoin_json_filename = p_sourcesjoin_json_filename
		
		self.m_pages = []
		self.m_pages_by_book_dict = {}

		self.ingest()

	def associate_person_to_page(self, p_json_entry):
		
		# "Page_Associated_Person_Join_Id":"1",
		# "Page_Id_Join":"1",
		# "Associated_Person_Id_Join":"2",
		# "Associated_Person_Role":"Author/Writer",
		# "Creator_Identification_Method":"Google",
		# "Creator_item_desc":"",
		# "Creator_item_links":""

		for index in range(len(self.m_pages)):

			if p_json_entry["Page_Id_Join"] == self.m_pages[index]["id"]:

				person_id = p_json_entry["Associated_Person_Id_Join"]
				
				# Associate the person to this page
				self.m_pages[index]["people_ids"].append(person_id)

				# Indicate what roles this person plays on this page
				if person_id not in self.m_pages[index]["people_roles"]:
					self.m_pages[index]["people_roles"][person_id] = []
				self.m_pages[index]["people_roles"][person_id].append(p_json_entry["Associated_Person_Role"])

				break

	def associate_place_to_page(self, p_json_entry):

		# "Page_Places_Named_Join":"1",
		# "Page_Id_Join_5":"3",
		# "Places_Named_Id_Join":"1"

		for index in range(len(self.m_pages)):
			if p_json_entry["Page_Id_Join_5"] == self.m_pages[index]["id"]:
				if "" == p_json_entry["Places_Named_Id_Join"]:
					continue
				self.m_pages[index]["places_ids"].append(p_json_entry["Places_Named_Id_Join"])
				break

	def associate_source_to_page(self, p_json_entry):

		# "Page_Associated_Sources_Join_Id":"1",
		# "Page_Id_Join_2":"1",
		# "Associated_Sources_Id_Join":"1",
		# "Sources_Identification_Method":"Google",
		# "Source_year_on_page":"",
		# "Source_additional_date_info":"",
		# "Source_link_to_page_content":"",
		# "Page_Associated_Sources_Join_notes":""		
		
		for index in range(len(self.m_pages)):
			if p_json_entry["Page_Id_Join_2"] == self.m_pages[index]["id"]:
				self.m_pages[index]["sources_ids"].append(p_json_entry["Associated_Sources_Id_Join"])
				break

	def debug_output(self):

		for page in self.m_pages:
			print page

	def debug_stats(self):

		for page in self.m_pages:
			print page["stats"]

	def ingest(self):

		# 1. Read and sort pages JSON
		self.ingest_helper(self.m_page_json_filename, self.save_page)
		self.m_pages = sorted(self.m_pages, key=lambda x: int(x["book_id"]), reverse=False)

		# Populate the pages by book dict
		for page in self.m_pages:
			if page["book_id"] not in self.m_pages_by_book_dict:
				self.m_pages_by_book_dict[page["book_id"]] = []
			self.m_pages_by_book_dict[page["book_id"]].append(page)

		# 2. Add associated person IDs to pages
		self.ingest_helper(self.m_peoplejoin_json_filename, self.associate_person_to_page)

		# 3. Add associated place IDs to pages
		self.ingest_helper(self.m_placesjoin_json_filename, self.associate_place_to_page)

		# 4. Add associated source IDs to pages
		self.ingest_helper(self.m_sourcesjoin_json_filename, self.associate_source_to_page)

	def ingest_helper(self, p_filename, p_save_function):

		with open(p_filename, "rU") as input_file:

			# Read the JSON
			my_json = json.loads(input_file.read())

			# Save each entry
			for entry in my_json["RECORDS"]:
				p_save_function(entry)			
				
	def save_page(self, p_json_entry):

		# "Page_Id":"1",
		# "Page_number":"215",
		# "Page_Number_suffix":"c",
		# "Scrapbook_Id":"1",
		# "Page_desc":"Cover page for Scrapbook 1..."
		# "Page_foldout":"N",
		# "Page_clipping_count":"7",
		# "Page_clipping_w_metadata_count":"2",
		# "Page_keywords":"Title Page, Paradise Lost, Nativity, Animals, Bear, Art, Metadata",
		# "Page_UKAT_keyword":"UKAT2.75 Natural Sciences; Animals, UKAT2.75 Natural sciences; Bears, UKAT3.20 Religion, UKAT3.35 Languages; French (language), UKAT3.40 Literature; Poetry, UKAT3.50 Visual arts, UKAT3.55 Performing arts; Lute, UKAT3.55 Performing arts; Musical Instruments, UKAT4.40 Family; Parents, UKAT5.10 Communication research and policy; Handwriting, UKAT5.15 Information management; Metadata, UKAT8.15 People and roles; Women, UKAT8.15 People and roles; Men, UKAT8.15 People and roles; Children (Age Group)",
		# "Page_clipping_orientations":"portrait",
		# "Page_original_material":"Y",
		# "Page_notes":"",
		# "Page_image_id":"MS_Morgan_C_1_0001"
		
		self.m_pages.append({

			"id": p_json_entry["Page_Id"],
			"number": p_json_entry["Page_number"],
			"suffix": p_json_entry["Page_Number_suffix"],
			"book_id": p_json_entry["Scrapbook_Id"],
			"desc": format_description(p_json_entry["Page_desc"]),
			"foldout": p_json_entry["Page_foldout"],
			"clippings": int(p_json_entry["Page_clipping_count"]),
			"clippings_w_metadata": int(p_json_entry["Page_clipping_w_metadata_count"]),
			"keywords": p_json_entry["Page_keywords"].split(", "),
			"ukat_keywords": p_json_entry["Page_UKAT_keyword"].split(", "),
			"orientations": p_json_entry["Page_clipping_orientations"].split(", "),
			"orig_material": p_json_entry["Page_original_material"],
			"notes": p_json_entry["Page_notes"],
			"people_ids": [],			
			"places_ids": [],
			"sources_ids": [],
			"people_roles": {},

			# Stats section
			"stats": {
			
				"people_dates_lived": {},
				"people_nationalities": {},
				"people_genders": {},
				"people_epithets": {},

				"place_counts_dict": {},

				"sources_places": {},
				"source_dates": {},
				"sources_rights_holders": {},

				"continent_counts": {},
			}
		})

	def save_stats(self, p_people, p_places, p_sources):

		for page in self.m_pages:

			# Collect stats about the people on each page		
			for person in p_people.m_people:

				if person["id"] in page["people_ids"]:

					# Date of birth/Date of death
					# NOTE: Range test to be implemented
					# update_stat(date_range_fn(person["dob"], person["dod"], 
					# 			  page["stats"]["date_ranges_lived"])

					# Nationality
					update_stat(person["nationality"], page["stats"]["people_nationalities"])

					# Gender
					update_stat(person["gender"], page["stats"]["people_genders"])

					# Profession
					update_stat(person["epithets"], page["stats"]["people_epithets"])

			# Collect stats about the sources on each page
			for source in p_sources.m_sources:

				if source["id"] in page["sources_ids"]:

					# Original publication place
					update_stat(source["place"], page["stats"]["sources_places"])

					# Original publication date
					# NOTE: Range test to be implemented
					# update_stat(date_range_fn2(source["date"],
					# 			  page["stats"]["source_dates"])

					# Publisher
					update_stat(source["rights_holder"], page["stats"]["sources_rights_holders"])

			# Collect stats about the places on each page
			for place in p_places.m_places:

				if place["id"] in page["places_ids"]:

					# Continent
					update_stat(place["continent"], page["stats"]["continent_counts"])

	
class WfsPeople:

	def __init__(self, p_people_json_filename):

		self.m_people_json_filename = p_people_json_filename
		self.m_people = []
		self.m_people_dict = {}
		self.ingest()

	def debug_output(self):

		print "\nPeople\n=============================\n"
		for person in self.m_people:
			print person
		print "\nPeople Dict\n=============================\n"
		for person_id in self.m_people_dict:
			print person_id
			print self.m_people_dict[person_id]

	def find_associated_books_and_pages(self, p_pages):

		# Save a list of associated pages for each person
		for person in self.m_people:
			for page in p_pages.m_pages:

				# If the person is on this page, include book and page IDs on its association lists
				if person["id"] in page["people_ids"]:

					if page["book_id"] not in person["stats"]["book_and_page_ids"]:
						person["stats"]["book_and_page_ids"][page["book_id"]] = []

					person["stats"]["book_and_page_ids"][page["book_id"]].append(page["id"])

	def ingest(self):

		with open(self.m_people_json_filename, "rU") as input_file:

			# Read the JSON
			people_json = json.loads(input_file.read())

			# Save each person entry
			for entry in people_json["RECORDS"]:
				self.save_person(entry)

			# Sort the people
			self.m_people = sorted(self.m_people, key=lambda x: int(x["id"]), reverse=False)

		# Make a dictionary of people by ID
		self.make_dict()

	def make_dict(self):

		# Create a dict for people by ID
		for person in self.m_people:
			if person["id"] not in self.m_people_dict:
				self.m_people_dict[person["id"]] = person
			else:
				print "Duplicate person listings for {0}".format(person) 

	def output(self, p_output_path):

		# Filename w/ name format wfs_people.json
		output_filename = "wfs_people.json"
		
		# Output the people dictionary
		with open(p_output_path + output_filename, "w") as output_file:
			output_file.write(json.dumps(self.m_people_dict))

	def save_person(self, p_json_entry):
		
		# "Associated_Person_Id":"1",
		# "Associated_Person_first_name":"Edwin",
		# "Associated_Person_last_name":"Morgan",
		# "Associated_Person_dob":"27 April 1920",
		# "Associated_Person_dod":"17 August 2010",
		# "Associated_Person_nationality":"Scottish",
		# "Associated_Person_gender":"Male",
		# "Associated_Person_title_profession":"Dr., Poet Makar",
		# "Associated_Person_additional_names":"",
		# "Associated_Person_link":"http://www.edwinmorgan.com/menu.html"
		# "Associated_Person_viaf":"http://viaf.org/viaf/68969203"

		self.m_people.append({

			"id": p_json_entry["Associated_Person_Id"],
			"name": p_json_entry["Associated_Person_first_name"] + " " +
					p_json_entry["Associated_Person_last_name"],
			"birth": p_json_entry["Associated_Person_dob"],
			"birth_sep": get_obj_from_dd_month_year(p_json_entry["Associated_Person_dob"]),
			"death": p_json_entry["Associated_Person_dod"],
			"death_sep": get_obj_from_dd_month_year(p_json_entry["Associated_Person_dod"]),
			"nationality": p_json_entry["Associated_Person_nationality"],
			"gender": p_json_entry["Associated_Person_gender"],
			# "title": p_json_entry["Associated_Person_title_profession"],
			"epithets": p_json_entry["Associated_Person_epithets"],
			"addl_names": p_json_entry["Associated_Person_alternate_names"],
			"link": p_json_entry["Associated_Person_link"],
			"viaf": p_json_entry["Associated_Person_viaf"],

			"stats": {

				# Co-occurrences
				"people_ids": [],
				"places_ids": [],
				"sources_ids": [],
				"keywords_ids": [],
				"ukat_keywords_ids": [],

				"book_and_page_ids": {},

				"people_on_pages_dict": {},
				"places_on_pages_dict": {},
				"sources_on_pages_dict": {},
			},
		})

	def save_stats(self, p_pages):

		# Find all people, places, and sources that occur on the same pages as these people
		find_associated_pps(self.m_people, p_pages, "people_ids")

		# Find all keywords that occur on the same pages as these people
		find_associated_keywords(self.m_people, p_pages, "people_ids")

		# Find all books and pages associated with these people
		self.find_associated_books_and_pages(p_pages)


class WfsPlaces:

	def __init__(self, p_places_json_filename):

		self.m_places_json_filename = p_places_json_filename
		self.m_places = []
		self.m_places_dict = {}
		self.ingest()

	def debug_output(self):

		print "\nPlaces\n=============================\n"
		for place in self.m_places:
			print place
		print "\nPlaces Dict\n=============================\n"
		for place_id in self.m_places_dict:
			print place_id
			print self.m_places_dict[place_id]

	def find_associated_books_and_pages(self, p_pages):

		# Save a list of associated pages for each place
		for place in self.m_places:
			for page in p_pages.m_pages:

				# If the place is on this page, include book and page IDs on its association lists
				if place["id"] in page["places_ids"]:

					if page["book_id"] not in place["stats"]["book_and_page_ids"]:
						place["stats"]["book_and_page_ids"][page["book_id"]] = []

					place["stats"]["book_and_page_ids"][page["book_id"]].append(page["id"])

	def ingest(self):

		with open(self.m_places_json_filename, "rU") as input_file:
		
			# Read the JSON
			places_json = json.loads(input_file.read())

			# Save each place entry
			for entry in places_json["RECORDS"]:
				self.save_place(entry)

			# Sort the places
			self.m_places = sorted(self.m_places, key=lambda x: int(x["id"]), reverse=False)

		# Make a dictionary of places by ID
		self.make_dict()

	def make_dict(self):

		# Create a dict for places by ID
		for place in self.m_places:
			if place["id"] not in self.m_places_dict:
				self.m_places_dict[place["id"]] = place
			else:
				print "Duplicate place listings for {0}".format(place) 

	def output(self, p_output_path):

		# Filename w/ name format wfs_places.json
		output_filename = "wfs_places.json"
		
		# Output the places dictionary
		with open(p_output_path + output_filename, "w") as output_file:
			output_file.write(json.dumps(self.m_places_dict))

	def save_place(self, p_json_entry):

		# "Place_Id":"1",
		# "Place_name":"Babylon",
		# "Place_name_variations":"",
		# "Place_name_countries":"ancient Mesopotamia",
		# "Place_name_continents":"Asia",
		# "Place_name_WOEID":"",
		# "Place_name_geonames_lat":"N 32deg 32' 27''",
		# "Place_name_geonames_long":"E 44deg 25' 27''",
		# "Place_name_geoname_link":"http://www.geonames.org/98228/babylon.html"


		self.m_places.append({

			"id": p_json_entry["Place_Id"],
			"name": p_json_entry["Place_name"],
			"addl_names": p_json_entry["Place_name_variations"],
			"countries": p_json_entry["Place_name_countries"],
			"continent": p_json_entry["Place_name_continents"],
			"woeid": p_json_entry["Place_name_WOEID"],
			"lat": p_json_entry["Place_name_geonames_lat"],
			"long": p_json_entry["Place_name_geonames_long"],
			"geolink": p_json_entry["Place_name_geoname_link"],

			"stats": {
				# Co-occurrences
				"people_ids": [],
				"places_ids": [],
				"sources_ids": [],
				"keywords_ids": [],
				"ukat_keywords_ids": [],
				"book_and_page_ids": {},
				"people_on_pages_dict": {},
				"places_on_pages_dict": {},
				"sources_on_pages_dict": {},
			},
		})

	def save_stats(self, p_pages):

		# Find all people, places, and sources that occur on the same pages as these places
		find_associated_pps(self.m_places, p_pages, "places_ids")	

		# Find all keywords that occur on the same pages as these places
		find_associated_keywords(self.m_places, p_pages, "places_ids")

		# Find all books and pages associated with these places
		self.find_associated_books_and_pages(p_pages)


class WfsSources:

	def __init__(self, p_sources_json_filename, p_sources_people_join_json_filename):

		self.m_sources_json_filename = p_sources_json_filename
		self.m_sources_people_join_json_filename = p_sources_people_join_json_filename
		self.m_sources = []
		self.m_sources_dict = {}
		self.ingest()

	def debug_output(self):

		print "\nSources\n=============================\n"
		for source in self.m_sources:
			print source
		print "\nSources Dict\n=============================\n"
		for source_id in self.m_sources_dict:
			print source_id
			print self.m_sources_dict[source_id]

	def find_associated_books_and_pages(self, p_pages):

		# Save a list of associated pages for each source
		for source in self.m_sources:
			for page in p_pages.m_pages:

				# If the source is on this page, include book and page IDs on its association lists
				if source["id"] in page["sources_ids"]:

					if page["book_id"] not in source["stats"]["book_and_page_ids"]:
						source["stats"]["book_and_page_ids"][page["book_id"]] = []

					source["stats"]["book_and_page_ids"][page["book_id"]].append(page["id"])

	def ingest(self):
		
		with open(self.m_sources_json_filename, "rU") as input_file:
		
			# Read the JSON
			sources_json = json.loads(input_file.read())

			# Save each source entry
			for entry in sources_json["RECORDS"]:
				self.save_source(entry)

			# Sort the sources
			self.m_sources = sorted(self.m_sources, key=lambda x: int(x["id"]), reverse=False)

		# Make a dictionary of sources by ID
		self.make_dict()

		# Associate creators with sources
		with open(self.m_sources_people_join_json_filename, "rU") as input_file:

			# Read the JSON
			sources_people_join_json = json.loads(input_file.read())

			# Associate creators with sources
			for entry in sources_people_join_json["RECORDS"]:
				self.save_source_people_join(entry)

	def make_dict(self):

		# Create a dict for sources by ID
		for source in self.m_sources:
			if source["id"] not in self.m_sources_dict:
				self.m_sources_dict[source["id"]] = source
			else:
				print "Duplicate source listings for {0}".format(source) 

	def output(self, p_output_path):

		# Filename w/ name format wfs_sources.json
		output_filename = "wfs_sources.json"
		
		# Output the sources dictionary
		with open(p_output_path + output_filename, "w") as output_file:
			output_file.write(json.dumps(self.m_sources_dict))

	def save_source(self, p_json_entry):

		# "Page_Associated_Sources_Id":"1",
		# "Page_Associated_Sources_name":"Paradise Lost",
		# "Page_Associated_Sources_associated_place":"",
		# "Page_Associated_Sources_date":"1667",
		# "Page_Associated_Source_rights_holder":"",
		# "Page_Associated_Sources_type_of_source":"Source Poem/Literature",
		# "Page_Associated_Sources_link":"http://ota.ox.ac.uk/text/3023.html",
		# "Page_Associated_Sources_notes":""

		self.m_sources.append({

			"id": p_json_entry["Page_Associated_Sources_Id"],
			"name": p_json_entry["Page_Associated_Sources_name"],
			"place": p_json_entry["Page_Associated_Sources_associated_place"],
			"date": p_json_entry["Page_Associated_Sources_date"],
			"rights_holder": p_json_entry["Page_Associated_Source_rights_holder"],
			"source_type": p_json_entry["Page_Associated_Sources_type_of_source"],
			"link": p_json_entry["Page_Associated_Sources_link"],
			"notes": p_json_entry["Page_Associated_Sources_notes"],

			"stats": {
				# Co-occurrences
				"people_ids": [],
				"places_ids": [],
				"sources_ids": [],
				"keywords_ids": [],
				"ukat_keywords_ids": [],
				"book_and_page_ids": {},
				"people_on_pages_dict": {},
				"places_on_pages_dict": {},
				"sources_on_pages_dict": {},

				"creators": [],
				"creators_notes": []
			},
		})

	def save_source_people_join(self, p_json_entry):

		# "Sources_Person_Join_Id":"1",
		# "Associated_Sources_Id_Join_2":"1",
		# "Associated_Person_Id_Join_2":"2",
		# "Sources_Person_Join_notes":""

		if p_json_entry["Associated_Sources_Id_Join_2"] in self.m_sources_dict:
			
			self.m_sources_dict[p_json_entry["Associated_Sources_Id_Join_2"]]["stats"]["creators"].append(
				p_json_entry["Associated_Person_Id_Join_2"])

			if len(p_json_entry["Sources_Person_Join_notes"]) > 0:
				self.m_sources_dict[p_json_entry["Associated_Sources_Id_Join_2"]]["stats"]["creators_notes"].append(
					p_json_entry["Sources_Person_Join_notes"])			

		else:
			print "Could not find source with ID {0} in sources_dict".format(
				p_json_entry["Associated_Sources_Id_Join_2"])

	def save_stats(self, p_pages):

		# Find all people, places, and sources that occur on the same pages as these sources
		find_associated_pps(self.m_sources, p_pages, "sources_ids")

		# Find all keywords that occur on the same pages as these sources
		find_associated_keywords(self.m_sources, p_pages, "sources_ids")

		# Find all books and places associated with these sources
		self.find_associated_books_and_pages(p_pages)


class WfsKeywords: 

	def __init__(self, p_scrapbooks, p_pages):

		# Keywords collection helps with statistics collection
		self.m_keywords = []

		# Full json will include two lookup tables for either direction
		self.m_keywords_json = { "ids": {}, 
								 "keywords": p_scrapbooks.m_collection["stats"]["keywords_to_ids"] }

		# Build initial tables 
		# (rest will be filled out by people, places, sources according books/pages associations)
		for id in p_scrapbooks.m_collection["stats"]["ids_to_keywords"]:

			# Build ID table (main table)
			self.m_keywords_json["ids"][id] = {
				"keyword": p_scrapbooks.m_collection["stats"]["ids_to_keywords"][id],
				"books": [],
				"pages": [],
				"people": [],
				"places": [],
				"sources": []
			}

			self.m_keywords.append({

				"id": p_scrapbooks.m_collection["stats"]["ids_to_keywords"][id],
				"stats": {
					# Co-occurrences
					"people_ids": [],
					"places_ids": [],
					"sources_ids": [],
					"keywords": [],

					"people_on_pages_dict": {},
					"places_on_pages_dict": {},
					"sources_on_pages_dict": {}
				}

			})

		self.save_stats(p_scrapbooks, p_pages)

		# Copy over stats to object being written to json (ad hoc fix)
		for id in p_scrapbooks.m_collection["stats"]["ids_to_keywords"]:
			for index in range(len(self.m_keywords)):
				if self.m_keywords[index]["id"] == self.m_keywords_json["ids"][id]["keyword"]:
					self.m_keywords_json["ids"][id]["stats"] = self.m_keywords[index]["stats"]


	def output(self, p_output_path):

		# Filename w/ name format wfs_keywords.json
		output_filename = "wfs_keywords.json"
		
		# Output the keywords dictionary
		with open(p_output_path + output_filename, "w") as output_file:
			output_file.write(json.dumps(self.m_keywords_json))

	def save_stats(self, p_scrapbooks, p_pages):

		# Associate each keyword by people, places, and sources on book pages
		for book in p_scrapbooks.m_books:

			for page in p_pages.m_pages_by_book_dict[book["id"]]:

				if book["id"] == page["book_id"]:

					for id in self.m_keywords_json["ids"]:

						if self.m_keywords_json["ids"][id]["keyword"] in page["keywords"]:

							# Associate this keyword to this book and page
							self.m_keywords_json["ids"][id]["books"].append(book["number"])
							self.m_keywords_json["ids"][id]["pages"].append(page["id"])

							# Associate this keyword to these people, places, and sources
							self.m_keywords_json["ids"][id]["people"].extend(page["people_ids"])
							self.m_keywords_json["ids"][id]["places"].extend(page["places_ids"])
							self.m_keywords_json["ids"][id]["sources"].extend(page["sources_ids"])

		# De-dupe all ID association lists for keywords
		for id in self.m_keywords_json["ids"]:
			self.m_keywords_json["ids"][id]["books"] = list(set(self.m_keywords_json["ids"][id]["books"]))
			self.m_keywords_json["ids"][id]["pages"] = list(set(self.m_keywords_json["ids"][id]["pages"]))
			self.m_keywords_json["ids"][id]["people"] = list(set(self.m_keywords_json["ids"][id]["people"]))
			self.m_keywords_json["ids"][id]["places"] = list(set(self.m_keywords_json["ids"][id]["places"]))
			self.m_keywords_json["ids"][id]["sources"] = list(set(self.m_keywords_json["ids"][id]["sources"]))

		# Find all people, places, and sources that occur on the same pages as these keywords
		find_associated_pps(self.m_keywords, p_pages, "keywords")			


def main():

	# print anchor_routes_from_formatted_text("This is |Edwin Morgan[1]|", "/collection/person")

	# 1. Path and filename definitions

	# Date of JSON files
	# json_file_date = "20180206"
	# json_file_date = "20180327"
	# json_file_date = "20180405"
	# json_file_date = "20180409"
	# json_file_date = "20180613"
	# json_file_date = "20181014"
	# json_file_date = "20190830"
	json_file_date = "20191025"

	# JSON paths
	input_path = os.getcwd() + os.sep + "input" + os.sep + json_file_date + os.sep
	output_path = os.getcwd() + os.sep + "output" + os.sep

	# Book JSON
	scrapbooks_json_filename = input_path + "Scrapbook_{0}.json".format(json_file_date)
	pages_json_filename = input_path + "Scrapbook_Page_{0}.json".format(json_file_date)

	# Book things JSON
	people_json_filename = input_path + "Page_Associated_People_{0}.json".format(json_file_date)
	places_json_filename = input_path + "Page_Places_Named_{0}.json".format(json_file_date)
	sources_json_filename = input_path + "Page_Associated_Sources_{0}.json".format(json_file_date)

	# Book joins JSON
	page_people_join_json_filename = input_path + "Page_People_Join_{0}.json".format(json_file_date)
	page_places_join_json_filename = input_path + "Page_Places_Named_Join_{0}.json".format(json_file_date)
	page_sources_join_json_filename = input_path + "Page_Associated_Sources_Join_{0}.json".format(json_file_date)
	
	# Sources JSON
	sources_people_join_json_filename = input_path + "Sources_People_Join_{0}.json".format(json_file_date)


	# 2. Ingest JSON in hierarchical fashion, from leaves up to root(s)

	# Ingest people, places, sources json
	people = WfsPeople(people_json_filename)
	places = WfsPlaces(places_json_filename)
	sources = WfsSources(sources_json_filename, sources_people_join_json_filename)	

	# Ingest pages json
	pages = WfsPages(pages_json_filename,
					 page_people_join_json_filename,
					 page_places_join_json_filename,
					 page_sources_join_json_filename)

	# Ingest book json
	scrapbooks = WfsScrapBooks(scrapbooks_json_filename)

	# 3. Save statistics

	# Save page statistics
	pages.save_stats(people, places, sources)

	# Save book statistics
	scrapbooks.save_stats(pages)

	# Save people statistics
	people.save_stats(pages)

	# Save places statistics
	places.save_stats(pages)

	# Save sources statistics
	sources.save_stats(pages)

	# Secondary statistics

	# Add source type count to collection stats
	scrapbooks.save_source_types(sources)

	# Add role type count to collection stats
	scrapbooks.save_people_roles(pages)

	# Add continent count to collection stats
	scrapbooks.save_continent_counts()

	# 4. Output one collection json and amalgamated json per book
	scrapbooks.output(pages, output_path)

	# 5. Output dictionary json for people, places, sources
	people.output(output_path)
	places.output(output_path)
	sources.output(output_path)

	# 6. Create keywords object (created later because of need for collection stats)
	keywords = WfsKeywords(scrapbooks, pages)

	# 7. Output dictionary json for keywords
	keywords.output(output_path)


if "__main__" == __name__:
	main()