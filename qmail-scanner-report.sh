#!/bin/sh
cd /var/spool/qmailscan

# using 'yesterday' here causes strange effects when DST changes.
day="${1:-1 day ago}"
mask=`LANG=C date -d "$day" '+%a, %d %b %Y '`

header="Virus report for $(LANG=C date -d "$day" '+%Y/%m/%d')"

if tty -s; then
	echo "$header"
else
	tmp=`mktemp ${TMPDIR:-/tmp}/qrepXXXXXX`
	mail=1
	exec 1>$tmp
fi

out=$(awk -F'\t' "/^$mask/ {print \$5} " < quarantine.log | sort | uniq -c | sort -nr)
total=`echo "$out" | awk '{a+=$1}END{print a}'`

cat <<EOF

$(printf "%7d Total" $total)
---------------------------
$out
EOF

# 1079  awk -F'\t' '{print $5}'< quarantine.log |sort |uniq -c|sort -nr
# 1083  awk -F'\t' '{if (!a) a=$1; b=$1} END{print "Start:", a, "\nEnd:", b}' < quarantine.log

if [ "$mail" ]; then
	install -m644 $tmp reports/$(LANG=C date -d "$day" '+%Y%m%d').txt
	mail -s "$(hostname -s): $header" ${MAILTO:-$LOGNAME} < $tmp
	rm $tmp
fi
