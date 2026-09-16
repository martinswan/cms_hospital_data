# CMS Hospitals data downloader

A script that downloads all data sets related to the theme "Hospitals" from the CMS provider data metastore. 

The column names in the csv headers are stored in mixed case with spaces and special characters. This converts all column names to snake_case (Example: "Patients’ rating of the facility linear mean score" becomes "patients_rating_of_the_facility_linear_mean_score").  

The csv files are downloaded and processed in parallel, and the job is designed to be run every day, and only download files that have been modified since the previous run.

Writes the results to `output/`. Tests for the column name conversion to snake_case are included.

## How it works

First, the script gets the list of Hospitals data sets from the metastore json and compares each one's modified date to what is in state.json. Anything new or changed goes on the process list.

The downloads run in a thread pool. Each worker downloads one csv from the process list, renames the headers, and writes the file to output/. Workers just return a result saying what happened and do not touch the state file on their own.

The main thread reads those results as they come in and only writes to state.json
when one succeeds. All the state stays in one thread so there is nothing to lock. If a data file fails, it is not updated in the state file, so the next run will pick it up and try again.

## Usage

### install:

Needs Python 3.11 or newer.

```bash
pip install -r requirements.txt
```

### run:

```bash
python download_cms_hospitals_data_sets.py
```

### test:

```bash
pytest
```

## Known limitations

- A download that fails is simply retried on the next daily run. This could be improved with some sort of metered retry.
- Did not implement logging.
- state.json stores the state as it knows it. If someone modifies that file or deletes the existing output, it will not be accurate.
- Collisions in file names and column names can occur, but this was not handled in this code because it was not observed here. All file names were unique and all column names are unique within each file. However, this could be added as a defensive measure.