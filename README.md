# Get started

In host,
```shell
docker build --tag mf:latest .
docker run -dt --name mf -v $(pwd)/resources/workspace:/root/workspace -v $(pwd)/coverage_xmls:/root/coverage_xmls mf:latest
docker exec -it mf bash
```
running this command will execute a docker container with Defects4J ([D4J](https://github.com/rjust/defects4j)) installed.

# Measure the coverage of transplanted failing test cases
In the container,
```shell
cd workspace
python3.6 create_multi.py [project] [v1:recentest]b [..]b [..]b [vn:oldest]b
```

For example,
```shell
python3.6 create_multi.py Lang 3b 4b 5b
```

If you run the above command, the failing test cases of `Lang-3b` and `Lang-4b` are transplanted to `Lang-5b`.

If you want to inspect the multi-faults subject, you can see the directory `/tmp/Lang-3b-4b-5b` in container.

In the directory, we are able to find `tests.trigger.expected` (the union of the triggering tests: ground-truth), and `tests.trigger` (the actual triggering tests in the merged version).
The two files are supposed to be identical if all faults (`Lang-3b`, `Lang-4b`) exist in `Lang-5b`.

Also, the coverage of the transplanted test cases are measured using Cobertura.

The coverage data will be saved to `/root/coverage_xmls/Lang-3b-4b-5b/` (in container) and `./coverage_xmls/Lang-3b-4b-5b/` (in host).

If you want to generate multi faults dataset for all D4J faults (Closure, Lang, Chart, Time, and Math), use following command:
```shell
python3.6 create_dataset.py
```

Actually, the coverage of all multi-fault subjects [already exist](./coverage_xmls/) in this repository.

# Create the coverage matrix of multi-fault subjects

To generate the whole coverage matrix of a multi-faults subject, e.g., `Lang-3b-4b-5b`,
we can append the coverage of transplanted test cases to the coverage of the oldest faulty version, `Lang-5b` for `Lang-3b-4b-5b`.

### 1. Create the coverage matrix of oldest faulty version
So, we first need to generate the coverage matrix of the oldest faulty version.

In a docker container, you can use the following script,
```shell
sh measure_coverage.sh [project] [version]
# sh measure_coverage.sh Lang 5b
```
Note that it takes quite long time to measure the whole coverage data.
So, we recommend you to distribute this task to multiple machines if you want to measure the coverage for all D4J faults.
The coverage data will be saved to `/root/coverage_xmls/Lang-5b/` (in container) and `./coverage_xmls/Lang-5b/` (in host).

By default, the line-level coverage is calculated for all classes in the project.
However, to speed up, you can only measure the coverage for relevant classes (the classes loaded by failing test cases).
Open `measure_coverage.sh` and replace the `classes.all` in Line 21 to `classes.relevant`.

After all coverage files are generated, create the coverage matrix (pandas dataframe):
```shell
python gen_coverage_matrix.py ./coverage_xmls/[project]-[version]/ -o ./data/[project]-[version].pkl
# python gen_coverage_matrix.py ./coverage_xmls/Lang-5b/ -o ./data/Lang-5b.pkl
```

### 2. Append the coverage of transplanted failing test cases
Run following command in host.
```shell
python gen_coverage_matrix.py ./coverage_xmls/project]-[v1]b-...-[vn]b -m ./data/[project]-[vn].pkl -o ./data/project]-[v1]b-...-[vn]b/.pkl
# python gen_coverage_matrix.py ./coverage_xmls/Lang-3b-4b-5b -m ./data/Lang-5b.pkl -o ./data/Lang-3b-4b-5b.pkl
```

# Build Dataset Json file for Failure Clustering Experiment

The hypergraph-based failure clustering experiment takes a dataset (`.json`) as an input.
[build_dataset.py](./build_dataset.py) will generate the dataset for the experiment.
First, open `build_dataset.py` and set up the config variables as described in the code.
After setting the variables, run:

```shell
python build_dataset.py [project]+ [num_faults] [savepath]
# python build_dataset.py Lang 1 ./dataset/Lang-single-fault.json
# python build_dataset.py Lang,Chart,Math,Time,Closure 1 ./dataset/single-fault.json
# python build_dataset.py Lang,Chart,Math,Time,Closure 2 ./dataset/two-faults.json
```
(Refer to [build.sh](./build.sh) for more details.)

This will generate the dataset only for the valid multi-faults subjects (non-overlapping GT & all faults revealed).
```json
{
    ...,
    "Lang3b-Lang4b-Lang5b": {
        "coverage": "[repo_root]/data/Lang-3b-4b-5b.pkl",
        "failing_tests": {
            "Lang3b": "[repo_root]/resources/failing_tests/Lang/3",
            "Lang4b": "[repo_root]/resources/failing_tests/Lang/4",
            "Lang5b": "[repo_root]/resources/failing_tests/Lang/5"
        },
        "faulty_components": {
            "Lang3b": "[repo_root]/resources/faulty_methods/Lang/3",
            "Lang4b": "[repo_root]/resources/faulty_methods/Lang/4",
            "Lang5b": "[repo_root]/resources/faulty_methods/Lang/5"
        },
        "faulty_components_level": 0
    },
    ...
}
```