# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import calendar
import csv
import datetime
import json
import logging
from pathlib import Path
import requests
import typing

from requests_ratelimiter import LimiterSession


def add_months(orig_date: datetime.datetime, months: int):
    """Adds the specified number of months to the original date.

    Args:
        orig_date: The original datetime.date or datetime.datetime object.
        months: The number of months to add (can be negative).

    Returns:
        A new datetime object with the months added.
    """

    month = orig_date.month - 1 + months  # Adjust for month index starting at 0
    year = orig_date.year + month // 12
    month = month % 12 + 1
    day = min(orig_date.day, calendar.monthrange(year, month)[1])
    return orig_date.replace(year=year, month=month, day=day)


def process(item_names, all_items):
    processed = {}
    for item in item_names:
        children = [
            f"{i['prefix']}:{i['name']}" for i in all_items if i["parent"] == item]
        if children:
            subnodes = process(children, all_items)
        else:
            subnodes = []
        processed[item] = subnodes
    return processed


def get_company(ticker: str,
                session: requests.Session) -> typing.Optional[typing.Dict[str, typing.Any]]:
    companies_json_url = "https://www.sec.gov/files/company_tickers.json"

    companies = session.get(companies_json_url).json().values()
    ticker = ticker.upper()
    companies = [c for c in companies if c["ticker"] == ticker]
    if len(companies) == 0:
        logging.error(f"Cannot find a company with ticker `%s`", ticker)
        return None
    return companies[0]


def get_filings(session: requests.Session,
                ticker: str,
                accession_numbers: typing.List[str],
                cache_dir: typing.Union[str, Path]) -> typing.Dict[str, str]:
    company = get_company(ticker, session)
    if not company:
        return {}
    files = {}
    cik_str = company["cik_str"]
    if isinstance(cache_dir, str):
        cache_dir = Path(cache_dir)
    cache_dir = cache_dir.joinpath(ticker.upper())
    cache_dir.mkdir(parents=True, exist_ok=True)
    accession_numbers = list(set(accession_numbers))
    for accn in accession_numbers:
        accn_file_name = f"{accn}.txt"
        accn_file = cache_dir.joinpath(accn_file_name)
        if accn_file.exists():
            files[accn] = accn_file.read_text(encoding="utf-8")
        else:
            filing_url = ("https://www.sec.gov/Archives/edgar/data/"
                          f"{cik_str}/{accn.replace('-', '')}/{accn_file_name}")
            filing = session.get(filing_url).text
            files[accn] = filing
            accn_file.write_text(filing, encoding="utf-8")
    return files


def get_company_facts(session: requests.Session,
                      ticker: str,
                      periods_after: typing.Optional[
                          typing.Union[str,
                                       datetime.date,
                                       datetime.datetime]
                      ] = None) -> typing.Dict:
    company = get_company(ticker, session)
    if not company:
        return {}
    company_name = company["title"]
    cik_str = company["cik_str"]
    cik_str_with_zeros = str(cik_str).zfill(10)

    company_info_url = ("https://data.sec.gov/submissions/"
                        f"CIK{cik_str_with_zeros}.json")
    info_json = session.get(company_info_url).json()
    fiscal_year_end = info_json["fiscalYearEnd"]
    fiscal_year_end = f"{fiscal_year_end[0:2]}-{fiscal_year_end[2:4]}"

    logging.info("Downloading company facts for %s (%s).",
                 company_name, ticker)

    facts_url = ("https://data.sec.gov/api/xbrl/companyfacts/"
                 f"CIK{cik_str_with_zeros}.json")
    facts_json = session.get(facts_url).json()

    if "us-gaap" not in facts_json["facts"]:
        logging.error("No US GAAP data in company facts.")
        return {}

    logging.info("Processing US GAAP data of %s (%s).",
                 facts_json["entityName"],
                 cik_str_with_zeros)
    us_gaap = facts_json["facts"]["us-gaap"]

    if periods_after:
        if isinstance(periods_after, datetime.datetime):
            periods_after = periods_after.date().isoformat()
        elif isinstance(periods_after, datetime.date):
            periods_after = periods_after.isoformat()
    else:
        periods_after = "0000-00-00"

    tag_data = {}
    for item in us_gaap.items():
        tag_data[item[0]] = {
            "label": item[1]["label"],
            "data": []
        }
        units = item[1]["units"]
        units_keys = list(units.keys())
        units_selected = units[units_keys[0]]
        units_key_selected = units_keys[0]
        if len(units) > 1:
            for i in range(1, len(units_keys)):
                if units_keys[i].startswith("USD"):
                    units_selected = units[units_keys[i]]
                    units_key_selected = units_keys[i]
                    break
        tag_data[item[0]]["units"] = units_key_selected
        for unit_item in units_selected:
            if unit_item["form"] in ["10-K", "10-Q"]:
                filed = unit_item["filed"]
                accn = unit_item["accn"]
                val = unit_item["val"]
                fp = unit_item["fp"]
                end_year = unit_item["end"].split("-")[0]
                fy_end_str = f"{end_year}-{fiscal_year_end}"
                fy_end = datetime.datetime.strptime(fy_end_str, "%Y-%m-%d")
                if fy_end.date().isoformat() <= periods_after:
                    continue
                fy_start_past = fy_end - datetime.timedelta(days=364)
                fy_start = datetime.datetime(fy_start_past.year,
                                             fy_start_past.month,
                                             1)
                fy = fy_end.year
                # Fiscal year in filings data is often wrong and linked to
                # the filing date.
                # Bu default, we assign it to the year of the end of the period.
                # For quarterly filings, we calculate it below.
                if fp.upper() == "FY":
                    end = fy_end
                    if unit_item["end"][5:] != fiscal_year_end:
                        # Skip if period is not aligned with fiscal year end
                        continue
                    start = fy_start
                else:
                    # Fiscal quarter data.
                    quarter = int(fp[1:])
                    if quarter == 4:
                        start = datetime.datetime(fy_end.year, fy_end.month, 1)
                        end = fy_end
                    else:
                        q_minus_one = quarter - 1
                        start = add_months(fy_start, q_minus_one * 3)
                        end = add_months(start, 3) - datetime.timedelta(1)
                if start.date().isoformat() <= periods_after:
                    continue
                data_item = {
                    "accn": accn,
                    "form": unit_item["form"],
                    "filed": filed,
                    "fiscal_year": fy,
                    "fiscal_period": fp,
                    "period_start_date": start.date().isoformat(),
                    "period_end_date": end.date().isoformat(),
                    "value": val
                }
                tag_data[item[0]]["data"].append(data_item)

    return tag_data


def store_facts(root_items, all_data, parent_path):
    for fact_item in root_items.items():
        name = fact_item[0].split(":")[-1]
        subnodes = fact_item[1]
        if subnodes:
            dir_path = parent_path.joinpath(name)
            file_name = "_self.json"
        else:
            dir_path = parent_path
            file_name = f"{name}.json"
        data_file_path = dir_path.joinpath(file_name)
        if name in all_data:
            dir_path.mkdir(parents=True, exist_ok=True)
            data_file_path.write_text(json.dumps(all_data[name], indent=4))
        if subnodes:
            store_facts(subnodes, all_data, dir_path)


def main():
    logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s",
                        level=logging.INFO,
                        force=True)
    tickers = ["GOOGL"]

    data_path = Path("data")
    data_path.mkdir(parents=True, exist_ok=True)
    session = LimiterSession(per_second=10)
    session.headers.update(
        {
            "User-Agent": "Google Cloud Cortex"
        }
    )

    # https://www.fasb.org/page/PageContent?pageId=/xbrl/gaap_meta_model_relationships_taxonomy.html
    with Path(__file__).parent.joinpath(
            "us_gaap_taxonomy_2024.csv").open(
            encoding="utf-8") as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))
    root_elements = [
        f"{r['prefix']}:{r['name']}" for r in rows if r["parent"].strip() == ""]
    tree = process(root_elements, rows)

    for ticker in tickers:
        company_path = data_path.joinpath(ticker.upper())
        company_path.mkdir(parents=True, exist_ok=True)
        facts = get_company_facts(session, ticker, "2013-12-31")

        accessions = []
        accession_forms = {}
        for fact in facts.values():
            for d in fact["data"]:
                accessions.append(d["accn"])
                accession_forms[d["accn"]] = d["form"]

        cache_dir = company_path.joinpath("_cache")
        filings = get_filings(session, ticker, accessions, cache_dir)
        for filing in filings.items():
            parsed_file = cache_dir.joinpath(f"{filing[0]}_parsed.json")
            if parsed_file.exists():
                all_sections = json.loads(
                    parsed_file.read_text(encoding="utf-8"))
            else:
                from prepline_sec_filings.sec_document import SECDocument
                from prepline_sec_filings.sections import SECTIONS_10K, SECTIONS_10Q

                filing_text = filing[1].split(
                    f"<TYPE>{accession_forms[filing[0]]}", 1)[-1]
                filing_text = filing_text.split("</DOCUMENT>", 1)[0]
                import re
                parts = re.split("<html>", filing_text, 1, flags=re.IGNORECASE)
                if len(parts) == 1:
                    filing_text = re.split(
                        "<html ", filing_text, 1, flags=re.IGNORECASE)[1]
                    filing_text = filing_text.split(">", 1)[-1]
                else:
                    filing_text = parts[1]
                filing_text = re.split(
                    "</html>", filing_text, 1, flags=re.IGNORECASE)[0]
                filing_text = f"<html>{filing_text}</html>"
                doc = SECDocument.from_string(filing_text)
                if not doc.filing_type:
                    doc.filing_type = accession_forms[filing[0]]
                if accession_forms[filing[0]] == "10-K":
                    sections = SECTIONS_10K
                else:
                    sections = SECTIONS_10Q
                all_sections = {}
                for sec in sections:
                    sec_texts = doc.get_section_narrative(sec)
                    if not sec_texts:
                        continue
                    texts = [n.text for n in sec_texts]
                    all_sections[str(sec)] = texts
                parsed_file.write_text(json.dumps(
                    all_sections, indent=2), encoding="utf-8")
            all_text = ""
            for sec in all_sections:
                sec_text = f"{str(sec).split('.')[-1]}:\n" + \
                    " ".join(all_sections[sec])
                all_text += sec_text + "\n\n"

        store_facts(tree, facts, company_path)


if __name__ == "__main__":
    main()
