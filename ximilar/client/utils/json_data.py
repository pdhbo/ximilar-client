import gzip
import json
import os
import string
import sys
from os.path import splitext


def read_json_array(file_name, required_fields=None, skip=0):
    with open(file_name, "r", encoding="utf-8") as f:
        array = json.load(f)
        for record in array:
            if skip > 0:
                skip -= 1
                continue
            if not required_fields or all(field in record for field in required_fields):
                yield record


def read_json_file_iterator(file_name, required_fields=None, skip=0):
    """
    This iterator method reads a file with JSON formatted lines, checks that every line has given field(s) and
    returns an iterator over JSON objects constructed from these lines.
    :param file_name: file with JSON formatted lines
    :param required_fields: list of fields that should be in each JSON object on the lines; lines not matching are not
            returned
    :return: an iterator over JSON objects that have given required fields
    """
    if splitext(file_name)[1] == ".gz":
        f = gzip.open(file_name, "rt", encoding="utf-8")
    else:
        f = open(file_name, "r", encoding="utf-8")

    chars_to_strip = string.whitespace + ","
    for line in f:
        line = line.rstrip(chars_to_strip)
        if skip > 0:
            skip -= 1
            continue
        try:
            record = json.loads(line)
        except UnicodeDecodeError as e:
            print("wrong encoding: '" + line + "'")
            continue
        except ValueError as e:
            print("JSON error: '" + line + "'")
            print(e)
            continue

        if not required_fields or all(field in record for field in required_fields):
            yield record
    f.close()


def read_json_file_list(file_name, required_fields=None, skip=0, is_array=False):
    data = []
    iterator = (
        read_json_array(file_name, required_fields, skip)
        if is_array
        else read_json_file_iterator(file_name, required_fields, skip)
    )
    for record in iterator:
        data.append(record)
    return data


class JSONWriter(object):
    """
    This class encapsulates a writer of JSON records into a potentially GZIPed file.
    """

    def __init__(self, file_name):
        if not file_name:
            self.output = sys.stdout
        else:
            if splitext(file_name)[1] == ".gz":
                self.output = gzip.open(file_name, "w")
            else:
                self.output = open(file_name, "w", encoding="utf-8")

    def __enter__(self):  # this is necessary to be used in "with statement"
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f"error processing JSON writer {str(exc_type)}, {str(exc_value)}, {str(traceback)}", file=sys.stderr)
        return self.close()

    def write(self, json_record, ensure_ascii=False, indent=None):
        json.dump(json_record, self.output, ensure_ascii=ensure_ascii, indent=indent)
        self.output.write("\n")
        self.output.flush()

    def close(self):
        if self.output is not sys.stdout:
            self.output.close()


def all_values(json_rec, field_name, subfield_name=None):
    """
    This is a helper function that, given a field name, returns an iterator over all values in the field regardless of
    if the field contains an array or a single value.
    :param json_rec: JSON record
    :param field_name: field to contain either array or a single value
    :return: iterator over the values
    """
    if field_name not in json_rec:
        return

    field = json_rec[field_name][subfield_name] if subfield_name else json_rec[field_name]

    if isinstance(field, list):
        for k in field:
            yield k
    else:
        yield field


def traverse_dir_to_json(output_file, directory):
    """
    Traverse a directory recursively and, for each file in the tree, add a single JSON line into an output JSON file:
    { "_file": "path/excluding/the/directory/file.ext" }
    :param output_file: JSON file to generate (it's overwritten if exists)
    :param directory: directory to traverse recursively
    :return: true, if the file was generated alright
    """
    output = JSONWriter(output_file)
    try:
        for subdir, dirs, files in os.walk(directory):
            for file_name in files:
                output.write({"_file": os.path.join(subdir, file_name)})
    finally:
        output.close()
