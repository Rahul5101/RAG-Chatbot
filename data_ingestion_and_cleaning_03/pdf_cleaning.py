
import re
import os
# from src_06.utils import load_config
# config = load_config()
# input_folder = config["data_ingestion"]["file_cleaning"]["input_folder"]
# output_folder = config["data_ingestion"]["file_cleaning"]["output_folder"]


def clean_pages(text):
    cleaned_lines = []
    current_page_content = []
    current_page_number = None

    for line in text.splitlines():
        line = line.strip()

        # Skip blank lines
        if not line:
            continue

        # Skip markdown table separators like |---|---|---|
        if re.fullmatch(r'\|[- ]+\|[- ]+\|[- ]+\|?', line):
            continue

        # Detect new page marker
        page_match = re.match(r"--- Page (\d+) ---", line)
        if page_match:
            if current_page_content and current_page_number:
                # Join and normalize spaces
                content = " ".join(current_page_content)
                content = re.sub(r"\s+", " ", content)
                cleaned_lines.append(f"Page {current_page_number}: {content}")
                current_page_content = []

            current_page_number = page_match.group(1)
            continue

        current_page_content.append(line)

    if current_page_content and current_page_number:
        content = " ".join(current_page_content)
        content = re.sub(r"\s+", " ", content)
        cleaned_lines.append(f"Page {current_page_number}: {content}")

    return "\n".join(cleaned_lines)


def process_all_files(input_root, output_root):
    """
    Traverse input_root -> subfolders -> text files,
    clean each text file, and save into output_root with same structure.
    """
    for subdir, _, files in os.walk(input_root):
        for filename in files:
            if filename.endswith(".txt"):
                input_path = os.path.join(subdir, filename)

                # Preserve relative path
                relative_path = os.path.relpath(subdir, input_root)
                output_dir = os.path.join(output_root, relative_path)
                os.makedirs(output_dir, exist_ok=True)

                output_path = os.path.join(output_dir, filename)

                # Read input file
                with open(input_path, "r", encoding="utf-8") as infile:
                    text = infile.read()

                # Clean text
                cleaned_text = clean_pages(text)

                # Save cleaned file
                with open(output_path, "w", encoding="utf-8") as outfile:
                    outfile.write(cleaned_text)

                print(f"✅ Cleaned: {input_path} -> {output_path}")


if __name__ == "__main__":
    input_folder = r"D:\valiance_sol\navy-wss\cleaned_file"          # your main folder with subfolders and txt files
    output_folder = r"D:\valiance_sol\navy-wss\final_cleaned_file" 

    process_all_files(input_folder, output_folder)
    print("🎉 All files cleaned and saved in dopt_final")






# import re
# import os
# import json


# def extract_case_between(text):
#     """
#     Extract case title like:
#     Avtar Singh v. ITO (2024) ...
#     Nataraj Ramaiah v. ITO (IT) (2024) ...
#     etc.
#     """
#     pattern = r"[A-Za-z\.\s]+v\.\s*[A-Za-z\(\)\s\.]*\(\d{4}\).*?(?=\sS\.|$)"
#     match = re.search(pattern, text)
#     return match.group(0).strip() if match else None



# def clean_pages(text):
#     pages = []
#     current_page_content = []
#     current_page_number = None

#     for line in text.splitlines():
#         line = line.strip()

#         # Skip empty lines
#         if not line:
#             continue

#         # Skip markdown-style separators
#         if re.fullmatch(r'\|[- ]+\|[- ]+\|[- ]+\|?', line):
#             continue

#         # Detect page header
#         page_match = re.match(r"--- Page (\d+) ---", line)
#         if page_match:
#             # Save previous page before starting new one
#             if current_page_content and current_page_number:
#                 full_text = " ".join(current_page_content)
#                 full_text = re.sub(r"\s+", " ", full_text)

#                 pages.append({
#                     "page_number": current_page_number,
#                     "text": full_text,
#                     "case_between": extract_case_between(full_text)
#                 })

#                 current_page_content = []

#             current_page_number = page_match.group(1)
#             continue

#         current_page_content.append(line)

#     # Save last page
#     if current_page_content and current_page_number:
#         full_text = " ".join(current_page_content)
#         full_text = re.sub(r"\s+", " ", full_text)

#         pages.append({
#             "page_number": current_page_number,
#             "text": full_text,
#             "case_between": extract_case_between(full_text)
#         })

#     return pages


# def process_all_files(input_root, output_root):
#     for subdir, _, files in os.walk(input_root):
#         for filename in files:
#             if filename.endswith(".txt"):
#                 input_path = os.path.join(subdir, filename)

#                 relative_path = os.path.relpath(subdir, input_root)
#                 output_dir = os.path.join(output_root, relative_path)
#                 os.makedirs(output_dir, exist_ok=True)

#                 output_path = os.path.join(output_dir, filename.replace(".txt", ".json"))

#                 # Read file
#                 with open(input_path, "r", encoding="utf-8") as infile:
#                     text = infile.read()

#                 # Clean & structure JSON
#                 page_data = clean_pages(text)

#                 # Save as JSON
#                 with open(output_path, "w", encoding="utf-8") as outfile:
#                     json.dump(page_data, outfile, indent=4, ensure_ascii=False)

#                 print(f" Saved JSON: {output_path}")



# if __name__ == "__main__":
#     input_folder = r"D:\valiance_sol\01_project\data_02\output_files\pdf_data"
#     output_folder = r"D:\valiance_sol\01_project\clean_04"

#     process_all_files(input_folder, output_folder)
#     print("🎉 All files cleaned and saved as JSON")








# import re
# import os

# def clean_pages(text):
#     cleaned_lines = []
#     current_page_content = []
#     current_page_number = None

#     for line in text.splitlines():
#         line = line.strip()

#         # Skip blank lines
#         if not line:
#             continue

#         # Skip markdown table separators like |---|---|---|
#         if re.fullmatch(r'\|[- ]+\|[- ]+\|[- ]+\|?', line):
#             continue

#         # Detect new page marker
#         page_match = re.match(r"--- Page (\d+) ---", line)
#         if page_match:
#             if current_page_content and current_page_number:
#                 # Join and normalize spaces
#                 content = " ".join(current_page_content)
#                 content = re.sub(r"\s+", " ", content)
#                 cleaned_lines.append(f"Page {current_page_number}: {content}")
#                 current_page_content = []

#             current_page_number = page_match.group(1)
#             continue

#         current_page_content.append(line)

#     if current_page_content and current_page_number:
#         content = " ".join(current_page_content)
#         content = re.sub(r"\s+", " ", content)
#         cleaned_lines.append(f"Page {current_page_number}: {content}")

#     return "\n".join(cleaned_lines)


# def process_all_files(input_root, output_root):
#     """
#     Traverse input_root -> subfolders -> text files,
#     clean each text file, and save into output_root with same structure.
#     """
#     for subdir, _, files in os.walk(input_root):
#         for filename in files:
#             if filename.endswith(".txt"):
#                 input_path = os.path.join(subdir, filename)

#                 # Preserve relative path
#                 relative_path = os.path.relpath(subdir, input_root)
#                 output_dir = os.path.join(output_root, relative_path)
#                 os.makedirs(output_dir, exist_ok=True)

#                 output_path = os.path.join(output_dir, filename)

#                 # Read input file
#                 with open(input_path, "r", encoding="utf-8") as infile:
#                     text = infile.read()

#                 # Clean text
#                 cleaned_text = clean_pages(text)

#                 # Save cleaned file
#                 with open(output_path, "w", encoding="utf-8") as outfile:
#                     outfile.write(cleaned_text)

#                 print(f"✅ Cleaned: {input_path} -> {output_path}")


# if __name__ == "__main__":
#     input_folder = "D:\valiance_sol\01_project\clean_04\cleaned_file\pdf_data"          # your main folder with subfolders and txt files
#     output_folder = "D:\valiance_sol\01_project\clean_04\final_cleaned_file"     # output folder

#     process_all_files(input_folder, output_folder)
#     print("🎉 All files cleaned and saved in dopt_final")










# import re
# import os
# import json

# # ----------------------------------------------------
# # REGEX PATTERNS
# # ----------------------------------------------------

# # Improved: Full case + citation (non-greedy, stops correctly)
# FULL_CASE_CITATION_REGEX = re.compile(
#     r"([A-Z][A-Za-z0-9\.\s&'’-]+ v\. [A-Z][A-Za-z0-9\.\s&'’()-]+"
#     r"\s*\(\d{4}\)[A-Za-z0-9\.\s/&,'’()-]*?)\s(?=[A-Z(])"
# )

# # Case name alone (parties only)
# CASE_NAME_ONLY_REGEX = re.compile(
#     # r"([A-Z][A-Za-z0-9\.\s&'’-]+ v\. [A-Z][A-Za-z0-9\.\s&'’()-]+)"
#     r"([A-Za-z0-9\.\'\-\s&]+ v\. [A-Za-z0-9\.\'\-\s&]+)"
# )

# # Section extraction
# SECTION_REGEX = (
#     r"(S\. ?\d+\([\dA-Za-z]+\)\([\dA-Za-z]+\)"
#     r"|S\. ?\d+\([\dA-Za-z]+\)"
#     r"|S\. ?\d+"
#     r"|Sec\. ?\d+\(?\d*[A-Za-z]*\)?"
#     r"|Section ?\d+\(?\d*[A-Za-z]*\)?)"
# )

# # Assessment year
# ASSESSMENT_YEAR_REGEX = (
#     r"(AY\. ?\d{4}-\d{2}"
#     r"|A\.Y\. ?\d{4}-\d{2}"
#     r"|Asst\. ?Yr\. ?\d{4}-\d{2}"
#     r"|Assessment Year ?\d{4}-\d{2})"
# )


# # ----------------------------------------------------
# # EXTRACTORS
# # ----------------------------------------------------

# def extract_section(text):
#     match = re.search(SECTION_REGEX, text, flags=re.IGNORECASE)
#     return match.group(0) if match else None


# def extract_assessment_year(text):
#     match = re.search(ASSESSMENT_YEAR_REGEX, text, flags=re.IGNORECASE)
#     return match.group(0) if match else None


# # ----------------------------------------------------
# # FIXED — EXTRACT CASES FROM PAGE
# # ----------------------------------------------------

# def extract_cases_from_page(page_text):
#     matches = list(re.finditer(FULL_CASE_CITATION_REGEX, page_text))
#     cases = []

#     if not matches:
#         return []

#     for i, match in enumerate(matches):
#         citation_full = match.group(1).strip()
#         start = match.start()
#         end = matches[i+1].start() if (i+1 < len(matches)) else len(page_text)

#         full_block = page_text[start:end].strip()

#         # Extract clean case name
#         name_match = CASE_NAME_ONLY_REGEX.search(citation_full)
#         case_name = name_match.group(1).strip() if name_match else citation_full

#         # Extract case body: full text minus citation
#         case_body = full_block.replace(citation_full, "").strip()
#         case_body = re.sub(r"\s+", " ", case_body)

#         cases.append({
#             "case_name": case_name,       # parties only
#             "citation": citation_full,    # full citation including parties
#             "case_body": case_body,       # everything after citation
#             "text": full_block            # for section detection
#         })

#     return cases


# # ----------------------------------------------------
# # PAGE SPLITTING
# # ----------------------------------------------------

# def clean_pages(text):
#     pages = []
#     current_page_text = []
#     current_page_number = None

#     for line in text.splitlines():
#         line = line.strip()
#         if not line:
#             continue

#         page_match = re.match(r"--- Page (\d+) ---", line)
#         if page_match:
#             if current_page_text and current_page_number:
#                 full_text = " ".join(current_page_text)
#                 full_text = re.sub(r"\s+", " ", full_text)
#                 pages.append({
#                     "page_number": current_page_number,
#                     "raw_text": full_text
#                 })
#             current_page_text = []
#             current_page_number = page_match.group(1)
#             continue

#         current_page_text.append(line)

#     if current_page_text and current_page_number:
#         full_text = " ".join(current_page_text)
#         full_text = re.sub(r"\s+", " ", full_text)
#         pages.append({
#             "page_number": current_page_number,
#             "raw_text": full_text
#         })

#     return pages


# # ----------------------------------------------------
# # MAIN PROCESSOR
# # ----------------------------------------------------

# def process_all_files(input_root, output_root):
#     uid = 1

#     for subdir, _, files in os.walk(input_root):
#         for filename in files:
#             if filename.endswith(".txt"):

#                 input_path = os.path.join(subdir, filename)
#                 rel_path = os.path.relpath(subdir, input_root)
#                 output_dir = os.path.join(output_root, rel_path)
#                 os.makedirs(output_dir, exist_ok=True)

#                 output_path = os.path.join(output_dir, filename.replace(".txt", ".json"))

#                 with open(input_path, "r", encoding="utf-8") as infile:
#                     text = infile.read()

#                 pages = clean_pages(text)
#                 final_output = []

#                 for page in pages:
#                     cases = extract_cases_from_page(page["raw_text"])

#                     for case in cases:
#                         case_text = case["text"]

#                         final_output.append({
#                             "id": uid,
#                             "page": int(page["page_number"]),
#                             "section_refs": ([extract_section(case_text)]
#                                              if extract_section(case_text) else []),
#                             "case_name": case["case_name"],
#                             "citation": case["citation"],
#                             "case_body": case["case_body"]
#                         })

#                         uid += 1

#                 with open(output_path, "w", encoding="utf-8") as outfile:
#                     json.dump(final_output, outfile, indent=4, ensure_ascii=False)

#                 print(f"✔ Processed {filename} → {output_path}")

#     print("\n🎉 ALL FILES PROCESSED SUCCESSFULLY!")


# # ----------------------------------------------------
# # RUN CONFIG
# # ----------------------------------------------------

# if __name__ == "__main__":
#     input_folder = r"D:\valiance_sol\01_project\data_02\output_files\pdf_data"
#     output_folder = r"D:\valiance_sol\01_project\clean_04"

#     process_all_files(input_folder, output_folder)


