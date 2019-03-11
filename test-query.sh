url="http://127.0.0.1:19986"
file=test.json
cat $file
curl -v -H "Content-Type: application/json" -d @"${file}" "${url}"
echo ""
