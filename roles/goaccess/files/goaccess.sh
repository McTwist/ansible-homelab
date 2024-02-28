#!/bin/bash

# Log location
logs="/var/www/users/*/tmp/*/access.log"

# Go through each log, creating the html file
for log in $logs
do
    tmp="${log%/access.log}"
    nice -n 19 goaccess "${log}" -o "${tmp}/goaccess.html" &
done
