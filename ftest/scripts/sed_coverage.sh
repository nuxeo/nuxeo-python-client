#!/bin/sh
cov_file=$(find .. -name coverage.xml)
sed -i '' 's/filename="/filename="nuxeo\//g' $cov_file