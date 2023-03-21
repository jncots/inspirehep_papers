# The script extracts papers from an author and
# save it in a specific format (Academia Sinica IOP requirements)
# as json and excel files

from pyinspirehep import Client
import pandas as pd
import json
from pathlib import Path


# This is an example parsing function
# Adopted from http://theoryandpractice.org/2019/04/INSPIRE%20API/#.ZBlT-3ZBxnJ
def summarize_record(data, max_authors=10):
    mini_dict = dict()
    mini_dict.update({"title": data["titles"][0]["title"]})
    if len(data["authors"]) > max_authors:
        # mini_dict.update({'authors':[a['full_name'] for a in data['authors'][:max_authors]]+['et. al.']})
        mini_dict.update(
            {
                "authors": "; ".join(
                    [a["full_name"] for a in data["authors"][:max_authors]]
                    + ["et. al."]
                )
            }
        )
    else:
        mini_dict.update(
            {"authors": "; ".join([a["full_name"] for a in data["authors"]])}
        )
        # mini_dict.update({'authors':[a['full_name'] for a in data['authors']]})

    if "collaborations" in data:
        mini_dict.update({"collaboration": data["collaborations"][0]["value"]})

    if "arxiv_eprints" in data:
        mini_dict.update({"arxiv_eprint": data["arxiv_eprints"][0]["value"]})
        mini_dict.update(
            {"url": "https://arxiv.org/abs/" + data["arxiv_eprints"][0]["value"]}
        )

    if "legacy_creation_date" in data:
        mini_dict.update({"creation_date": data["legacy_creation_date"]})

    if "publication_info" in data:
        mini_dict.update(
            {"journal_title": data["publication_info"][0].get("journal_title", None)}
        )
        mini_dict.update(
            {"journal_volume": data["publication_info"][0].get("journal_volume", None)}
        )
        mini_dict.update(
            {"page_start": data["publication_info"][0].get("page_start", None)}
        )
        mini_dict.update(
            {"journal_year": data["publication_info"][0].get("year", None)}
        )

    if "dois" in data:
        mini_dict.update({"doi": data["dois"][0]["value"]})
    return mini_dict


# This is a implementation of above function for parsing records
# from INSPIRE API in a specific format
def parse_record_iop(data, max_authors=10, author_name="Fedynitch"):
    mini_dict = dict()

    # "Author List" column
    if len(data["authors"]) > max_authors:
        # mini_dict.update({'authors':[a['full_name'] for a in data['authors'][:max_authors]]+['et. al.']})
        mini_dict.update(
            {
                "Author List": "; ".join(
                    [a["full_name"] for a in data["authors"][:max_authors]]
                    + ["et. al."]
                )
            }
        )
    else:
        mini_dict.update(
            {"Author List": "; ".join([a["full_name"] for a in data["authors"]])}
        )
        # mini_dict.update({'authors':[a['full_name'] for a in data['authors']]})

    # "First Author" column
    field_val = "N"
    if author_name in data["authors"][0]["full_name"]:
        field_val = "Y"

    mini_dict.update({"First Author": field_val})
    # "Author for Correspondance" column
    mini_dict.update({"Author for Correspondance": field_val})

    # "Publishing Year" column
    publication_year = ""
    if "publication_info" in data:
        publication_year = data["publication_info"][0].get("year", "")

    mini_dict.update({"Publishing Year": publication_year})

    # "Publishing Month" column
    publication_month = ""
    imprints_date = ""
    if "imprints" in data:
        imprints_date = data["imprints"][0].get("date", "")
        if imprints_date and (len(imprints_date.split("-")) > 1):
            if publication_year:
                if imprints_date.split("-")[0].strip() == str(publication_year).strip():
                    publication_month = imprints_date.split("-")[1]

    mini_dict.update({"Publishing Month": publication_month})

    # "Title" column
    mini_dict.update({"Title": data["titles"][0]["title"]})

    # "Language" column
    mini_dict.update({"Language": "Non-Chinese"})

    # "Journal Title" column
    journal_title = ""
    if "publication_info" in data:
        journal_title = data["publication_info"][0].get("journal_title", None)
    mini_dict.update({"Journal Title (Non-Mandarin)": journal_title})

    # "Status" column
    if "publication_info" in data:
        mini_dict.update({"Status": "Published"})
    else:
        mini_dict.update({"Status": "Accepted"})

    # "Volumn & Page Number" column
    vol_page = ""
    if "publication_info" in data:
        volume = data["publication_info"][0].get("journal_volume", "")
        page_start = data["publication_info"][0].get("page_start", "")
        page_end = data["publication_info"][0].get("page_end", "")

        vol_page = f"{volume}"

        if page_start:
            vol_page = f"{vol_page}, {page_start}"
            if page_end:
                vol_page = f"{vol_page}-{page_end}"

    mini_dict.update({"Volumn & Page Number": vol_page})

    # Other columns
    if "dois" in data:
        mini_dict.update({"DOI": data["dois"][0]["value"]})

    if "arxiv_eprints" in data:
        mini_dict.update({"e-Print": data["arxiv_eprints"][0]["value"]})

    mini_dict.update({"Publication date": imprints_date})

    return mini_dict


path_to_save = Path(__file__).parent
author = "Fedynitch"
# Maximum number of authors
# Format: max authors + et al
# Large number (e.g. 1000) for all
max_authors = 10
# Maximum number of articles
# Large number (e.g. 1000) for all
number_of_articles = 1000


# Get a json data from inspirehep rest-api
# Get maximum 1000 records ordered from recent to oldest
client = Client()
literature = client.search_literature(size=number_of_articles, q=f"a {author}")

# Parse records from received json
parsed_records = []
for i in range(len(literature["hits"]["hits"])):
    record = literature["hits"]["hits"][i]["metadata"]
    summary = parse_record_iop(record, max_authors=max_authors, author_name=author)
    parsed_records.append(summary)

result_json = json.dumps(parsed_records, indent=4)

# Output to json
output_file = path_to_save / "papers.json"
with open(output_file, "w") as f:
    f.write(result_json)

# Output to excel
output_file = path_to_save / "papers.xlsx"
pandas_data = pd.read_json(result_json)
pandas_data.to_excel(output_file, index=False)
