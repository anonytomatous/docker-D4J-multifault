import argparse
import os
import logging
import subprocess
import shlex
import json
import re
import numpy as np
import xml.etree.ElementTree as ET
import pandas as pd
from tqdm import tqdm

dir_path = os.path.dirname(os.path.realpath(__file__))

def get_hits(cov_file_path):
    tree = ET.parse(cov_file_path)
    root = tree.getroot()
    # key: (class_name, method_name, signature)
    # value: hitcount
    hits = {}
    packages = root[1]
    for package in packages:
        for classes in package:
            for _class in classes:
                class_name = _class.attrib["name"]
                class_file_name = _class.attrib["filename"]
                line_rate = float(_class.attrib["line-rate"])
                num_lines = len(_class[1])
                #if line_rate > 0 and num_lines > 0:
                #    print(class_name, line_rate)
                for method in _class[0]:
                    method_name = method.attrib["name"]
                    method_signature = method.attrib["signature"]
                    args_type = method_signature[1:].split(')')[0]
                    method_id = "{}${}<{}>".format(class_name, method_name, args_type)
                    for line in method[0]:
                        hits[(method_id, line.attrib["number"])] = int(line.attrib["hits"])
    return hits

def check_validity(log_path, verbose=False):
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log = json.load(f)
            if verbose:
                logging.info("Overlapped: {}, Union: {}".format(log["overlapped"], log["union"]))
            return log["valid"]
    else:
        return False

def is_combined_well(coverage_dir, verbose=False):
    is_valid = check_validity(os.path.join(coverage_dir, "log.json"), verbose=verbose)
    has_transplant_error = os.path.exists(os.path.join(coverage_dir, ".transplant_error"))
    has_compile_error = os.path.exists(os.path.join(coverage_dir, ".compile_error"))
    if verbose:
        logging.info("Transplant Error: {}, Compile Error: {}".format(is_valid, has_transplant_error, has_compile_error))
    return is_valid and not has_transplant_error and not has_compile_error

def merge(coverage_dir, matrix_path, savepath):
    coverage_dir = os.path.abspath(coverage_dir)
    savepath = os.path.abspath(savepath)
    logging.info("Matrix path: {}".format(matrix_path))
    logging.info("Coverage dir: {}".format(coverage_dir))
    logging.info("Output path: {}".format(savepath))

    if matrix_path is not None and not is_combined_well(coverage_dir):
        logging.warning("Combining error: {}".format(coverage_dir))

    if matrix_path is not None:
        cov = pd.read_pickle(matrix_path)
    else:
        cov = pd.DataFrame() # Empty Dataframe
    logging.debug("Original shape: {}".format(cov.shape))

    if not os.path.exists(coverage_dir):
        raise Exception("No directory exists: {}".format(coverage_dir))

    for test in os.listdir(coverage_dir):
        if test[-4:] != ".xml":
            continue
        lines = cov.index.values.tolist()
        hits = get_hits(os.path.join(coverage_dir, test))
        new_lines = list(set(hits.keys()) - set(lines))
        #print(set(hits.keys()) - set(lines))
        #assert len(set(hits.keys()) - set(lines)) == 0
        coverage_vector = []
        for line in lines:
            coverage_vector.append(hits[line] if line in hits else 0)
        test_key = test[:-4].replace("::", ".")
        cov[test_key] = np.array(coverage_vector)
        if new_lines:
            testcases = cov.columns.values.tolist()
            row = [int(test==test_key) for test in testcases]
            new_rows = pd.DataFrame(
                [row[:] for i in range(len(new_lines))],
                index=new_lines,
                columns=testcases,
            )
            #print(new_rows)
            logging.debug("Appending {} new lines".format(len(new_lines)))
            cov = cov.append(new_rows)
        logging.debug("Adding {}: {}".format(test_key, cov.shape))
    cov.to_pickle(savepath)
    logging.info("Saved to {}".format(savepath))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("newdir", type=str)
    parser.add_argument("--matrix", "-m", type=str, default=None)
    parser.add_argument("--savepath", "-o", type=str, default="output.pkl")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    merge(args.newdir, args.matrix, args.savepath)