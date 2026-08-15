First create data/raw for input csv
and output for output the result

create src/__init__.py to mark it as package and ensure easy imports though it works but its a convention

generate fake data -> generate_sample_data.py

one file to run at root so ->pipeline.py

create requirements.txt and readme.md

now write dependencies in requirements.txt
then run pip install -r requirements.txt

we create src/config.py
so now for every csv file we need some facts data about it so in config.py we use dataclass for storing of data, annotation for type hints avoid errors

why for dataclass we kept slots as true and frozen as true
`frozen=True` — locks existing fields (like `file_name`) so they can't be silently changed after creation, avoiding bugs like accidentally reading the wrong file.
`slots=True` — blocks creating brand-new, unplanned attributes (like a typo'd field name), so mistakes get caught instantly instead of silently existing as dead data.


file_name is what to actually open on disk; name is the short, clean label used everywhere else (logs, errors, lookups) instead of the clunky full filename.

key_column- its stores like one column like say order_id

requirecol for validation

datecol for datecol -optional so write default 

chunk - size of chunk -options so wrote default

then for every csv we write in respective of variables 

next create exceptions.py 

and now think in the process of 

read ->validate->reconcile (matching or merging )->transform     what errors can occur 
so write errors such that they can cover a class of errors under the hood for example datasourceerror class represent filenotfound error, fileformat error, directory error all under once class


so after exceptions.py the next we do is create logging_config.py why this because this is the most shared dependency file so writing it first is a logical step

reading csv and returning a cleaned dataframe is the common task we need to do 
so we create adapters.py and there what all write is
imports
pandas - as we need csvs
Path- instead of c:\\users we get Path()
while we wait before retrying - time 
do we log process - import logging

after all importing so first focus is on reading

so 
create SourceAdapter class get the initialize the values from sourceconfig , raw_dir and then initialize variables like config and path 

then in _read_raw here _ before convention for this method is internal helper dont call it from outside
reading is done in chunks and at last concat

then after reading now this is the time for validating the schema like is the required columns are correct or any missing _validate_schema
if missing raise schemavalidationerror

now next logical function _clean so remved duplicates and convrted datecolumn to there datetime and if type of col is object strip whitespace

config.py
    ↓
Stores dataset configuration

exceptions.py
    ↓
Custom exceptions

adapters.py
    ↓
Read → Validate → Clean

reconcile.py
    ↓
Aggregate → Join → Build trusted dataset

report.py
    ↓
Generate Markdown report

benchmark.py
    ↓
Measure Pandas vs Polars performance

pipeline.py
    ↓
Orchestrate the entire workflow