import argparse
import os
import json

TMP_DIR = os.environ['TMP_DIR']
COVERAGE_DIR = os.environ['COVERAGE_DIR']

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=str)
    parser.add_argument("versions", type=str, nargs='+')
    parser.add_argument("--retry", "-r", action="store_true")
    args = parser.parse_args()

    assert len(args.versions) > 1
    i = len(args.versions) - 2
    for i in reversed(range(len(args.versions) - 1)):
        recent = args.versions[i]
        old = '-'.join(args.versions[i+1:])
        merged = '-'.join(args.versions[i:])

        old_dir = "{}/{}-{}".format(TMP_DIR, args.project, old)
        recent_dir = "{}/{}-{}".format(TMP_DIR, args.project, recent)
        merged_dir = "{}/{}-{}".format(TMP_DIR, args.project, merged)

        old_cov_dir = "{}/{}-{}".format(COVERAGE_DIR, args.project, old)
        merged_cov_dir = "{}/{}-{}".format(COVERAGE_DIR, args.project, merged)

        print("============================================================")
        print("Creating {} by combining {} and {}...".format(merged, old, recent))
        print("------------------------------------------------------------")

        is_old_valid = True
        if os.path.exists(os.path.join(old_cov_dir, "log.json")):
            is_old_valid = is_combined_well(old_cov_dir)

        if not is_old_valid:
            break

        combine = True
        if os.path.exists(merged_dir) and os.path.exists(merged_cov_dir):
            # if it wasn't combined properly try again
            if not args.retry or is_combined_well(merged_cov_dir):
                combine = False

        if combine:
            os.system("sh combine.sh {} {} {} {}".format(args.project, recent, old, merged))

        # validity check
        if os.path.exists(merged_dir):

            has_common_fts = False
            if is_old_valid:
              with open(os.path.join(old_dir, "tests.trigger"), 'r') as f:
                  old_fts = set([ l.strip() for l in f.readlines()])
              with open(os.path.join(recent_dir, "tests.trigger"), 'r') as f:
                  recent_fts = set([ l.strip() for l in f.readlines()])

              overlapped = old_fts.intersection(recent_fts)
              has_common_fts = len(overlapped) > 0

            with open(os.path.join(merged_dir, "tests.trigger.expected"), 'r') as f:
                expected = set([ l.strip() for l in f.readlines()])
            with open(os.path.join(merged_dir, "tests.trigger"), 'r') as f:
                actual = set([ l.strip() for l in f.readlines()])

            info = {
                "overlapped": has_common_fts,
                "union": expected == actual,
                "valid": not has_common_fts and (expected == actual),
                "failing_tests": {
                    "expected": list(expected),
                    "actual": list(actual)
                }
            }
            with open(os.path.join(merged_cov_dir, "log.json"), 'w') as f:
                json.dump(info, f, indent=4)

            print("- Dir            :", merged_dir)
            print("- Cov            :", merged_cov_dir)
            print("- #EFT           :", len(expected))
            print("- #AFT           :", len(actual))
            print("- Overlapped (O) :", has_common_fts)
            print("- Union (U)      :", expected == actual)
            print("- Valid (!O&U)   :", not has_common_fts and (expected == actual))
        print("============================================================")
        print()
