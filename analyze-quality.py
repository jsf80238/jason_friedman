import argparse
import logging
import os
import pathlib
import random
import sys
# Imports above are standard Python
# Imports below are 3rd-party
from argparse_range import range_action
import pandas as pd
from dateutil.parser import parse
import numpy as np

DEFAULT_MAX_DETAIL_VALUES = 35
UP_ARROW = "⤒"
DOWN_ARROW = "⤓"
MAX_SHEET_NAME_LENGTH = 31  # Excel limitation

ROW_COUNT = "count"
NULL_COUNT = "null"
NULL_PERCENT = "%null"
UNIQUE_COUNT = "unique"
UNIQUE_PERCENT = "%unique"
MOST_COMMON = "most_common"
MOST_COMMON_PERCENT = "%most_common"
LARGEST = "largest"
SMALLEST = "smallest"
LONGEST = "longest"
SHORTEST = "shortest"
MEAN = "mean"
PERCENTILE_25TH = "percentile_25th"
MEDIAN = "median"
PERCENTILE_75TH = "percentile_75th"
STDDEV = "stddev"

ANALYSIS_LIST = (
    ROW_COUNT,
    NULL_COUNT,
    NULL_PERCENT,
    UNIQUE_COUNT,
    UNIQUE_PERCENT,
    MOST_COMMON,
    MOST_COMMON_PERCENT,
    LARGEST,
    SMALLEST,
    LONGEST,
    SHORTEST,
    MEAN,
    PERCENTILE_25TH,
    MEDIAN,
    PERCENTILE_75TH,
    STDDEV,
)

parser = argparse.ArgumentParser(
    description='Analyze the quality of a CSV file.',
    epilog='Generates an Excel workbook containing the analysis.'
)
parser.add_argument('input', help="/path/to/file.csv.")
parser.add_argument('--header', type=int, metavar="NUM", help="Specify the number of rows to skip for header information.")
parser.add_argument('--max-detail-values', type=int, metavar="INT", action=range_action(1, 1e99), default=DEFAULT_MAX_DETAIL_VALUES, help=f"Produce this many of the top/bottom value occurrences, default is {DEFAULT_MAX_DETAIL_VALUES}.")
parser.add_argument('--sample-percent', type=int, metavar="INT", action=range_action(1, 99), help=f"Randomly choose this percentage of the input data and ignore the remainder.")
logging_group = parser.add_mutually_exclusive_group()
logging_group.add_argument('-v', '--verbose', action='store_true')
logging_group.add_argument('-t', '--terse', action='store_true')
args = parser.parse_args()
input_path = pathlib.Path(args.input)
max_detail_values = args.max_detail_values

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S %Z')
handler.setFormatter(formatter)
logger.addHandler(handler)
if args.verbose:
    handler.setLevel(logging.DEBUG)
elif args.terse:
    handler.setLevel(logging.WARNING)
else:
    handler.setLevel(logging.INFO)

if not input_path.exists():
    logger.critical(f"No such file '{args.input}'.")
    sys.exit(1)
else:
    output_path = (input_path.parent / input_path.stem).with_suffix(".xlsx")

logger.info(f"Reading from '{input_path}' ...")

skip_list = list()
if args.sample_percent:
    header_size = args.header or 1
    number_of_rows = sum(1 for line in open(input_path)) - header_size
    sample_size = int(args.sample_percent * number_of_rows / 100)
    skip_list = sorted(random.sample(range(header_size, number_of_rows+1), number_of_rows-sample_size))

if args.header:
    input_df = pd.read_csv(input_path, skiprows=skip_list, header=args.header)
else:
    input_df = pd.read_csv(input_path, skiprows=skip_list)


def parse_date(date):
    if date is np.nan:
        return np.nan
    else:
        return parse(date)


def truncate_string(s, max_length, filler="..."):
    """
    For example, truncate_string("Hello world!", 7) returns:
    "Hell..."
    """
    excess_count = len(s) - max_length
    if excess_count <= 0:
        return s
    else:
        return s[:max_length-len(filler)] + filler


def set_best_type(series):
    """
    Set the type so as to give the most interesting/useful analysis
    :param series: a Pandas/Numpy series
    :return: prefer in this order:
    * integer
    * float
    * date
    * string
    """
    try:
        series = series.astype('int')
        logger.debug("Integer column.")
    except Exception:
        logger.debug("Not an integer column.")
        try:
            series = series.astype('float')
            logger.debug("Float column.")
        except Exception:
            logger.debug("Not a float column.")
            try:
                series = series.apply(parse).astype('datetime64[ns]')
                # series = pd.to_datetime(series, infer_datetime_format=True)
                logger.debug("Datetime column.")
            except Exception:
                logger.debug("Not a datetime column.")
                logger.debug("String column.")
    return series


summary_dict = dict()  # To be converted into the summary worksheet
detail_dict = dict()  # Each element to be converted into a detail worksheet
for label in input_df.columns:
    logger.info(f"Working on column '{label}' ...")
    data = input_df[label]
    data = set_best_type(data)
    if False and not label == "activity_date":  # useful for debugging a single column, change False to True
        continue
    row_dict = dict.fromkeys(ANALYSIS_LIST)
    # Row count
    row_count = data.size
    row_dict[ROW_COUNT] = row_count
    # Null
    null_count = row_count - data.count()
    row_dict[NULL_COUNT] = null_count
    # Null%
    row_dict[NULL_PERCENT] = 100 * null_count / row_count
    # Unique
    unique_count = len(data.unique())
    row_dict[UNIQUE_COUNT] = unique_count
    # Unique%
    row_dict[UNIQUE_PERCENT] = 100 * unique_count / row_count

    # Detail dataframe
    detail_df = pd.DataFrame()

    if null_count != row_count:
        # Most common (mode)
        row_dict[MOST_COMMON] = list(data.mode().values)[0]
        # Most common%
        row_dict[MOST_COMMON_PERCENT] = 100 * list(data.value_counts())[0] / row_count

        if data.dtype == 'object':
            # Largest & smallest
            row_dict[LARGEST] = data.dropna().astype(pd.StringDtype()).max()
            row_dict[SMALLEST] = data.dropna().astype(pd.StringDtype()).min()
            # Longest & shortest
            row_dict[LONGEST] = max(data.dropna().astype(pd.StringDtype()).values, key=len)
            row_dict[SHORTEST] = min(data.dropna().astype(pd.StringDtype()).values, key=len)
            # No mean/quartiles/stddev statistics for strings
        else:  # numeric or datetime
            # Largest & smallest
            row_dict[LARGEST] = data.max()
            row_dict[SMALLEST] = data.min()
            # No longest/shortest for dates and numbers
            # Mean/quartiles/stddev statistics
            row_dict[MEAN] = data.mean()
            row_dict[PERCENTILE_25TH] = data.quantile(0.25)
            row_dict[MEDIAN] = data.quantile(0.5)
            row_dict[PERCENTILE_75TH] = data.quantile(0.75)
            row_dict[STDDEV] = data.std()

        # Value counts
        # Collect no more than number of values available or what was given on the command-line
        # whichever is less
        max_length = min(max_detail_values, len(data.value_counts(dropna=False)))
        # Create 3-column ascending visual
        detail_df["rank " + DOWN_ARROW] = list(range(1, max_length + 1))
        detail_df["value " + DOWN_ARROW] = list(data.value_counts(dropna=False).index)[:max_length]
        percent_total_list = list(data.value_counts(dropna=False, normalize=True))[:max_length]
        detail_df["%total " + DOWN_ARROW] = [x*100 for x in percent_total_list]
        # Visual spacing
        detail_df[" "] = [None] * max_length
        # Create 3-column descending visual
        last_rank = len(data.value_counts(dropna=False))
        detail_df["rank " + UP_ARROW] = list(range(last_rank, last_rank - max_length, -1))
        detail_df["value " + UP_ARROW] = list(data.value_counts(ascending=True, dropna=False).index)[:max_length]
        percent_total_list = list(data.value_counts(ascending=True, dropna=False, normalize=True))[:max_length]
        detail_df["%total " + UP_ARROW] = [x*100 for x in percent_total_list]

    summary_dict[label] = row_dict
    detail_dict[label] = detail_df

# Convert this dictionary of dictionaries to a DataFrame
result_df = pd.DataFrame.from_dict(summary_dict, orient='index')
# And write it to a worksheet
logger.info("Writing summary ...")
writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
result_df.to_excel(writer, sheet_name="Summary")
# And generate a detail sheet for each column
for label, detail_df in detail_dict.items():
    logger.info(f"Writing detail for column '{label}' ...")
    detail_df.to_excel(writer, index=False, sheet_name=truncate_string(label+" detail", MAX_SHEET_NAME_LENGTH))
writer.close()
logger.info(f"Wrote {os.stat(output_path).st_size} bytes to '{output_path}'.")
