import os
import logging
import sys
import json
from gen_coverage_matrix import is_combined_well

# ===========================================================================================
# <Usage> Using "sh build.sh" is recommended to generate entire dataset
# python build_dataset.py [project1,project2,...] [num_faults] [savepath]
# ex)
# python build_dataset.py Lang 1 ./dataset/Lang-single-fault.json
# python build_dataset.py Lang,Chart,Math,Time,Closure 1 ./dataset/single-fault.json
# python build_dataset.py Lang,Chart,Math,Time,Closure 2 ./dataset/two-faults.json
# ===========================================================================================
target_projects = sys.argv[1].split(',')
num_faults = int(sys.argv[2])
dataset_path = sys.argv[3]

logging.basicConfig(level=logging.INFO)

coverage_xmls = os.path.abspath("./coverage_xmls")
failing_test_path_fmt = "./resources/failing_tests/{0}/{1}"
faulty_methods_path_fmt = "./resources/faulty_methods/{0}/{1}"

# ===========================================================================================
# FIXME: Setup these variables
matrix_dir = os.path.abspath("./data/") # the location of multi-faults coverage matrix
matrix_path_fmt = "./data/{0}-{1}.pkl" # the path of single fault coverage matrix
# ===========================================================================================

projects = {
    "Lang": (1, 65),
    "Chart": (1, 26),
    "Time": (1, 27),
    "Math": (1, 106),
    "Closure": (1, 133)
}

deprecated = [
    ("Lang", 2), ("Time", 21), ("Closure", 63), ("Closure", 93)
]

dataset = {}

error = 0
if num_faults == 1:
    for project in target_projects:
        start, end = projects[project]
        for version in range(start, end+1):
            if (project, version) in deprecated:
                continue
            data_id = "{}{}b".format(project, version)
            failing_test_path = os.path.abspath(failing_test_path_fmt.format(project, version))
            faulty_method_path = os.path.abspath(faulty_methods_path_fmt.format(project, version))
            with open(failing_test_path) as f:
                num_failings = len(f.readlines())
            if not num_failings > 1:
                continue
            coverage_path = os.path.abspath(matrix_path_fmt.format(project, version))
            dataset[data_id] = {
                "coverage": coverage_path,
                "failing_tests": {
                    data_id: failing_test_path
                },
                "faulty_components": {
                    data_id: faulty_method_path
                },
                # 0: method, 1: line
                "faulty_components_level": 0
            }
elif num_faults >= 2:
    for fault_id in os.listdir(coverage_xmls):
        project = fault_id.split("-")[0]
        if project not in target_projects:
            continue
        versions = [v[:-1] for v in fault_id.split("-")[1:]]
        if len(versions) != num_faults:
            continue
        coverage_dir = os.path.join(coverage_xmls, fault_id)
        if not os.path.isdir(coverage_dir):
            continue
        if is_combined_well(coverage_dir):
            combined_matrix_path = os.path.join(matrix_dir, "{}.pkl".format(fault_id))
            data_id = "-".join(["{}{}b".format(project, v) for v in versions])
            dataset[data_id] = {
                "coverage": combined_matrix_path,
                "failing_tests": {
                    "{}{}b".format(project, version): os.path.abspath(failing_test_path_fmt.format(project, version))
                    for version in versions
                },
                "faulty_components": {
                    "{}{}b".format(project, version): os.path.abspath(faulty_methods_path_fmt.format(project, version))
                    for version in versions
                },
                # 0: method, 1: line
                "faulty_components_level": 0
            }
        else:
            logging.warning("{} is not combined properly".format(fault_id))
            is_combined_well(coverage_dir, verbose=True)
            error += 1

with open(dataset_path, "w") as f:
    json.dump(dataset, f, indent=4)

logging.info("{} data points are generate at {} ({} ommitted)".format(len(dataset), dataset_path, error))
