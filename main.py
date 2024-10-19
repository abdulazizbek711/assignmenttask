import pdfplumber
import json
import re
import os

import pdfplumber
import json
import re

pdf_path = "" # path to pdf file
output_json_path = "" # path to the output json file



def clean_title(title):
    # Remove page numbers, trailing dots, and extra spaces
    title = re.sub(r'\s*\.\.\.*\d+$', '', title)
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\.+$', '', title)
    return title.strip()

def merge_incomplete_titles(current_title, next_line):
    next_line_cleaned = clean_title(next_line)
    if next_line_cleaned and not re.match(r'^\d', next_line):
        return f"{current_title} {next_line_cleaned}"
    return current_title

def extract_structure(text):
    structure = {}
    current_chapter = current_section = current_subsection = None
    lines = text.splitlines()

    chapter_pattern = r'^(?:Глава|ГЛАВА)\s+(\d+)(?:\.|:)?\s*(.*)'
    section_pattern = r'^(\d+\.\d+\.?)\s+(.*)'
    subsection_pattern = r'^(\d+\.\d+\.\d+|\w+\)|\d+\))\s+(.*)'

    for i, line in enumerate(lines):
        line = line.strip()

        chapter_match = re.match(chapter_pattern, line, re.IGNORECASE)
        if chapter_match:
            chapter_number, chapter_title = chapter_match.groups()
            chapter_title = clean_title(chapter_title)
            if i + 1 < len(lines):
                chapter_title = merge_incomplete_titles(chapter_title, lines[i + 1])
            structure[chapter_number] = {"title": chapter_title if chapter_title else f"Глава {chapter_number}", "sections": {}}
            current_chapter = chapter_number
            current_section = current_subsection = None
            continue

        section_match = re.match(section_pattern, line)
        if current_chapter and section_match:
            section_number, section_title = section_match.groups()
            section_title = clean_title(section_title)
            if i + 1 < len(lines):
                section_title = merge_incomplete_titles(section_title, lines[i + 1])
            structure[current_chapter]["sections"][section_number] = {
                "title": section_title,
                "subsections": {}
            }
            current_section = section_number
            current_subsection = None
            continue

        subsection_match = re.match(subsection_pattern, line)
        if current_section and subsection_match:
            subsection_number, subsection_title = subsection_match.groups()
            subsection_title = clean_title(subsection_title)
            if i + 1 < len(lines):
                subsection_title = merge_incomplete_titles(subsection_title, lines[i + 1])
            structure[current_chapter]["sections"][current_section]["subsections"][subsection_number] = {
                "title": subsection_title
            }
            current_subsection = subsection_number
            continue

        if current_subsection and not subsection_match and not section_match and not chapter_match:
            structure[current_chapter]["sections"][current_section]["subsections"][current_subsection]["title"] += " " + line.strip()

    return structure

def main():
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

        with pdfplumber.open(pdf_path) as pdf:
            pdf_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

        if not pdf_text:
            raise ValueError("No text could be extracted from the PDF")

        extracted_structure = extract_structure(pdf_text)

        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(extracted_structure, json_file, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
