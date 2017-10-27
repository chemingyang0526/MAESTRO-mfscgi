#!/bin/bash
echo 'csv collect!'
NAME=`date '+cpu_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=91000"

NAME=`date '+memory_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90200"

NAME=`date '+deletion_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90020"

NAME=`date '+replication_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90030"

NAME=`date '+read_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90040"

NAME=`date '+write_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90050"

NAME=`date '+packets_received_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90060"

NAME=`date '+packets_write_m%m.d%d'`
rm -rf "/usr/share/mfscgi/csvdata/$NAME"
wget -O "/usr/share/mfscgi/csvdata/$NAME" "http://127.0.0.1:9425/chart.cgi?host=127.0.0.1&port=9421&id=90070"