Useful Links:

Ollama Github and Info: https://github.com/ollama/ollama

COMPANIES = [
    "Royal Bank of Canada",
    "TCW",
    "Lincoln Financial",
    "Natixis",
    "AssetMark",
    "Aristotle",
    "Pathstone",
    "Fidelity",
    "Orion",
   "NEPC",
   "Invesco",
    "Janney Montgomery Scott LLC",
    "Northern Trust",
    "SEI",
    "Macquarie Asset Management",
   "BNY Mellon",
    "AllianceBernstein",
   "Russell Investments",
    "NASDAQ",
    "JP Morgan",
    "Wells Fargo",
    "Apollo Global Management",
    "T. Rowe Price",
    "Capital Group",
    "Blackrock",
    "Vanguard",
    "Morgan Stanley",
    "Invesco",
    "Wellington Management",
    "Franklin Templeton",
    "KKR",
    "Oaktree Capital Management",
    "Voya Investment Management",
    "PIMCO",
    "Guggenheim Investments",
    "Principal Global Investments",
    "Brown Advisory"
    ]


File Info:

setup_login.py: run when using program for first time to initate scrapping tool.

indeed_pipeline_main.py: Initates complete pipeline using Indeed scrapper and Gemma3-12B model.

main_indeed.py: runs Indeed scrapper only

Local_LLM/RunModel.py: run LLM only


Run and initiate Modelfile:

1. cd to directory with Modelfile
2. Get base model: "ollama run gemma3:12b"
3. "ollama create baseModel_gemma -f Modelfile"
4.  verify creation: "ollama run baseModel_gemma"

