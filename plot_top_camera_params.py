#!/bin/python

import os
import exifread
import seaborn as sns
import pandas as pd
import pprint
import matplotlib.pyplot as plt
import argparse


# argument parser settings
arg_parser = argparse.ArgumentParser(prog='Plot most used EXIF parameters')
arg_parser.add_argument('dir', help='A directory containing image files')


# subset of EXIF tags
exif_subset = ['EXIF ExposureTime',
               'EXIF ISOSpeedRatings',
               'EXIF FocalLength',
               'EXIF FNumber']

# prettyPrint settings
pp = pprint.PrettyPrinter(indent=4)


# Iterate over all the key value pairs in dictionary and call the given
# callback function() on each pair. Items for which callback() returns True,
# add them to the new dictionary. In the end return the new dictionary.
#
# Arguments:
#   dict_obj -- dictionary object
#   callback -- function to filter the (key,value) pair
#
# Return:
#   <dict>
def filter_dict(dict_obj, callback):
    filtered_dict = dict()
    # Iterate over all the items in dictionary
    for (key, value) in dict_obj.items():
        # Check if item satisfies the given condition then add to new dict
        if callback((key, value)):
            filtered_dict[key] = value

    return filtered_dict


# Extract EXIF data from the file and filter that by the provided subset of tags
#
# Arguments:
#   f -- file for the EXIF data to be extracted from
#   tags_subset -- <list> of tags names (EXIF parameters)
#
# Return:
#   <list>
def collect_tags(f, tags_subset):
    # collect exif tags
    raw_tags = exifread.process_file(f)
    # select only desirable tags
    selected_tags = filter_dict(raw_tags, lambda elem: elem[0] in exif_subset)
    # calculate F number in tags and convert all tags to strings
    tags = dict((k, eval(str(v)) if k == 'EXIF FNumber' else str(v)) for k, v in selected_tags.items())

    return tags


# Select top used values of specified parameter and plot the result
#
# Arguments:
#   data -- <DataFrame> with the EXIFS
#   x -- name of the parameter/variable (column in a DataFrame)
#
# Return:
#   <pandas.Series>
def sel_top_vals(data, x):
    values = data[x]
    top_values_cnt_idx = values.value_counts().nlargest(10).index
    top_values = data[values.isin(top_values_cnt_idx)][x]

    return top_values


# Iterate through files in the directory and collect exifs
# for every single NEF or RAW file, skip other files
def harvest_exifs_from_dir(dir):
    tags = []
    for subdir, dirs, files in os.walk(dir):
        for filename in files:
            filepath = subdir + os.sep + filename
            ext = os.path.splitext(filepath)[-1].lower()

            if ext not in ('.nef', '.raw'):
                continue

            f = open(filepath, 'rb')

            # populate the list with exifs
            tags.append(collect_tags(f, exif_subset))

    return tags


def parse_arguments():
    args, unknown_args = arg_parser.parse_known_args()

    if unknown_args:
        print('Unknown argument(s):', unknown_args)
        arg_parser.print_help()

    return args


def main():
    args = parse_arguments()

    exifs_df = pd.DataFrame(harvest_exifs_from_dir(args.dir))
    # rename columns to a friendly format
    exifs_df.rename(columns={'EXIF ExposureTime': 'Shutter Speed',
                             'EXIF ISOSpeedRatings': 'ISO',
                             'EXIF FocalLength': 'Focal length',
                             'EXIF FNumber': 'F number'},
                    inplace=True)

    # set font size
    sns.set_context(rc={'font.size': 8})

    # create 4 axes to plot parameters
    fig = plt.figure()
    ax1 = fig.add_axes([0.05, 0.55, 0.42, 0.4])
    ax2 = fig.add_axes([0.05, 0.05, 0.42, 0.4])
    ax3 = fig.add_axes([0.55, 0.55, 0.42, 0.4])
    ax4 = fig.add_axes([0.55, 0.05, 0.42, 0.4])

    # build count plot for every parameter on a separate axes
    sorted_shutter_speeds = sel_top_vals(exifs_df, 'Shutter Speed').iloc[sel_top_vals(exifs_df, 'Shutter Speed').apply(lambda x: eval(x)).sort_values().index]
    sns.countplot(x=sorted_shutter_speeds, ax=ax1)
    sns.countplot(x=sel_top_vals(exifs_df, 'ISO'), ax=ax2)
    sns.countplot(x=sel_top_vals(exifs_df, 'Focal length'), ax=ax3)
    sns.countplot(x=sel_top_vals(exifs_df, 'F number'), ax=ax4)

    plt.show()


# Start point
if __name__ == '__main__':
    main()
