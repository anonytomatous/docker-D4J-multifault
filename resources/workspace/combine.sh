project=$1
recent=$2
old=$3
merged=$4
# The old version has the recent bug, but without the fault-revealing test.
# The merged version will have the "old code" and "recent test"

recent_dir=$TMP_DIR/$project-$recent
old_dir=$TMP_DIR/$project-$old
merged_dir=$TMP_DIR/$project-$merged
echo $recent_dir
echo $old_dir
echo $merged_dir

#
# 1.
# Checkout the recent version and export the properties
#
echo "Prepare $recent_dir"
[ ! -d $recent_dir ] && defects4j checkout -p $project -v $recent -w $recent_dir
cd $recent_dir;
[ ! -f tests.trigger ] && defects4j export -p tests.trigger -o tests.trigger;
[ ! -f classes.relevant ] && defects4j export -p classes.relevant -o classes.relevant;

#
# 2.
# Checkout the old version and export the properties
#
echo "Prepare $old_dir"
[ ! -d $old_dir ] && defects4j checkout -p $project -v $old -w $old_dir
cd $old_dir
[ ! -f tests.trigger ] && defects4j export -p tests.trigger -o tests.trigger;
[ ! -f classes.relevant ] && defects4j export -p classes.relevant -o classes.relevant;

#
# 3.
# Create directory for the merged fault (base: old version)
#
rm -rf $merged_dir
cp -r $old_dir $merged_dir
[ -d $COVERAGE_DIR/$project-$merged ] && rm -rf $COVERAGE_DIR/$project-$merged
mkdir $COVERAGE_DIR/$project-$merged
[ -d $COVERAGE_DIR/$project-$old ] && cp $COVERAGE_DIR/$project-$old/*.xml $COVERAGE_DIR/$project-$merged/

#
# 4.
# Go to the recent fault
# and copy the test files containing the fault-revealing tests
# to the merged fault directory (overwrite)
#
cd $recent_dir
test_src_dir=$(defects4j export -p dir.src.tests)
cat tests.trigger | uniq | while read testcase; do
  test_name=$(echo $testcase | grep "[^\:]*$" -o)
  test_class=$(echo $testcase | grep "^[^\:]*" -o)
  test_file="$test_src_dir/$(echo $test_class | sed 's/\./\//g').java"
  echo $test_class $test_file
  # diff $recent_dir/$test_file $old_dir/$test_file # print diff
  # if there is no directory, create directory
  [ ! -d $merged_dir/$(dirname "$test_file") ] && mkdir -p $merged_dir/$(dirname "$test_file")
  # if there is no file at destination, copy the source file
  [ ! -f $merged_dir/$test_file ] && cp $recent_dir/$test_file $merged_dir/$test_file
  # if the file exists at destination, overwrite the test methods
  # FIXME: only copy the test methods, not the entire test cases
  cp $merged_dir/$test_file $merged_dir/$test_file.orig
  python3.6 /root/workspace/move_test.py  $recent_dir/$test_file $merged_dir/$test_file $test_name
  if [ $? -eq 0 ]
  then
      echo "Successfully transplanting $test_name"
  else
      echo "Error detected during the transplant. Genereate .transplant_error"
      [ ! -f $merged_dir/.transplant_error ] && touch $merged_dir/.transplant_error
      echo $testcase >> $merged_dir/.transplant_error
  fi
  echo "===================="
  diff $merged_dir/$test_file.orig $merged_dir/$test_file
  echo "===================="
done

#
# 5.
# Take the union of the failing tests (tests.trigger.expected)
#
cd $merged_dir/
cat $recent_dir/tests.trigger > tests.trigger.expected
echo '\n' >> tests.trigger.expected;
cat $old_dir/tests.trigger >> tests.trigger.expected
sort tests.trigger.expected | uniq | awk 'NF' > tests.trigger.expected.uniq
mv tests.trigger.expected.uniq tests.trigger.expected

#
# 6.
# Run the tests and save the actual failing tests (tests.trigger)
#
rm -rf target/
defects4j compile
if [ ! $? -eq 0 ]; then
    touch $merged_dir/.compile_error
fi

timeout 10m defects4j test
if [ ! $? -eq 0 ]; then
    touch $merged_dir/.timeout_error
fi

if [ -f failing_tests ]; then
  grep "\-\-\- \K(.*)" failing_tests -oP > tests.trigger;
else
  touch tests.trigger
fi

#
# 7.
# Print the expected and actual failing tests
#
echo "=========== Ground Truth ==========="
cat tests.trigger.expected
echo "============== Actual =============="
sort tests.trigger

#
# 8.
# Figure out the classes that are loaded by failing tests of both old and recent faults
# and take the union of the two sets (classes.relevant)
# = classes that are loaded by either the old failing tests and the recent failing testss
#
cat $recent_dir/classes.relevant > classes.relevant
echo '\n' >> classes.relevant
cat $old_dir/classes.relevant >> classes.relevant
sort classes.relevant | uniq | awk 'NF' > classes.relevant.uniq
mv classes.relevant.uniq classes.relevant

#
# 9.
# Print the revelant classes (whose coverage should be measured)
#
echo "============== CLASSES =============="
cat classes.relevant

#
# 10.
# Measure the coverage of all failing tests
# on the merged (=old) version of the code
#
# measure the coverage of new test
sort $recent_dir/tests.trigger | while read test_method; do
  echo "Measuring coverage of $test_method .............."
  timeout 5m defects4j coverage -t $test_method -i classes.relevant
  if [ ! $? -eq 0 ]; then
      touch $merged_dir/.timeout_error
  else
    mv coverage.xml $COVERAGE_DIR/$project-$merged/$test_method.xml
  fi
done

cp .*_error $COVERAGE_DIR/$project-$merged
