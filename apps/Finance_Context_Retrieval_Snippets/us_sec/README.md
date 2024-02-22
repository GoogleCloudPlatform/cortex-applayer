# US GAAP data and filings narratives from US SEC

## DISCLAIMER

This code is for demonstration purposes only. It is not intended to be used in production.

## How to run

Run `xbrl_us_gaap_hier.py`.

It does 2 things:

1. Gathers (`get_company_facts`) and stores (`store_facts`) Company Facts (from 10-K and 10-Q filings) in a folder structure with `.json` files reflecting the US GAAP hierarchy (in `./data` folder).

2. Gathers and processes 10-K and 10-Q filings. Currently only prints and caches it. They can be summarized and/or used in question answering scenarios along with the Company Facts.

Files in `prepline_sec_filings are slightly modified versions of respective functions taken from [pipeline-sec-filings repo](https://github.com/Unstructured-IO/pipeline-sec-filings) (Apache-2.0 license). They are only used for processing 10-K and 10-Q narratives.
