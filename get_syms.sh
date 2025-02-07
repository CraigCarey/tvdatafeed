#! /usr/bin/env bash

set -eux

curl 'https://symbol-search.tradingview.com/symbol_search/v3/?text=&hl=1&country=US&lang=en&search_type=stocks&domain=production&sort_by_country=US' \
  -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.5' \
  -H 'Referer: https://www.tradingview.com/' \
  -H 'Origin: https://www.tradingview.com' \
  -H 'Connection: keep-alive' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'Priority: u=4' \
  --output syms0.json

curl 'https://symbol-search.tradingview.com/symbol_search/v3/?text=&hl=1&country=US&lang=en&search_type=stocks&start=50&domain=production&sort_by_country=US' \
  -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.5' \
  -H 'Referer: https://www.tradingview.com/' \
  -H 'Origin: https://www.tradingview.com' \
  -H 'Connection: keep-alive' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'Priority: u=4' \
  --output syms1.json
