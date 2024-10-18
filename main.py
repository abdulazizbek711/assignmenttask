import pdfplumber
import json
import re

pdf_path = "" # path to pdf file
output_json_path = "" # path to the output json file

def clean_title(title):
    title = re.sub(r"[\d.]+", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()

def merge_incomplete_titles(current_title, next_line):
    next_line_cleaned = clean_title(next_line)
    if next_line_cleaned and not re.match(r'^\d', next_line):
        return f"{current_title} {next_line_cleaned}"
    return current_title

def extract_structure(text):
    structure = {}
    current_chapter = current_section = None
    lines = text.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()

        # Detect chapters
        chapter_match = re.match(r"^Глава\s+(\d+)\s+(.*)", line)
        if chapter_match:
            chapter_number, chapter_title = chapter_match.groups()
            chapter_title = clean_title(chapter_title)
            if i + 1 < len(lines):
                chapter_title = merge_incomplete_titles(chapter_title, lines[i + 1])
            structure[chapter_number] = {"title": chapter_title, "sections": {}}
            current_chapter = chapter_number
            current_section = None
            continue

        section_match = re.match(r"^(\d+\.\d+)\s+(.*)", line)
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
            continue

        subsection_match = re.match(r"^(\d+\.\d+\.\d+)\s*(.*)", line)
        if current_section and subsection_match:
            subsection_number, subsection_title = subsection_match.groups()
            subsection_title = clean_title(subsection_title)
            if i + 1 < len(lines):
                subsection_title = merge_incomplete_titles(subsection_title, lines[i + 1])
            structure[current_chapter]["sections"][current_section]["subsections"][subsection_number] = {
                "title": subsection_title
            }

    return structure

def main():
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pdf_text = "\n".join(page.extract_text() for page in pdf.pages)
        extracted_structure = extract_structure(pdf_text)
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(extracted_structure, json_file, ensure_ascii=False, indent=4)

        print(f"Structure saved to: {output_json_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()