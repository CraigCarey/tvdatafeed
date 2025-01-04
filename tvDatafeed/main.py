import datetime
import enum
import json
import logging
import random
import re
import string
import pandas as pd
from websocket import create_connection
import requests
import json

logger = logging.getLogger(__name__)

set_data_quality_msg = "set_data_quality"
switch_timezone_msg = "switch_timezone"
set_auth_token_msg = "set_auth_token"
chart_create_session_msg = "chart_create_session"
quote_create_session_msg = "quote_create_session"
quote_set_fields_msg = "quote_set_fields"
quote_add_symbols_msg = "quote_add_symbols"
resolve_symbol_msg = "resolve_symbol"
quote_fast_symbols_msg = "quote_fast_symbols"
create_series_msg = "create_series"
symbol_resolved = "symbol_resolved"
series_completed = "series_completed"

fields = [
    "ch",
    "chp",
    "current_session",
    "description",
    "local_description",
    "language",
    "exchange",
    "fractional",
    "is_tradable",
    "lp",
    "lp_time",
    "minmov",
    "minmove2",
    "original_name",
    "pricescale",
    "pro_name",
    "short_name",
    "type",
    "update_mode",
    "volume",
    "currency_code",
    "rchp",
    "rtc",
]


class Interval(enum.Enum):
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"


class TvDatafeed:
    sign_in_url = "https://www.tradingview.com/accounts/signin/"
    search_url = "https://symbol-search.tradingview.com/symbol_search/v3/?text={}&hl=1&exchange={}&lang=en&&search_type=undefined&domain=production&sort_by_country=US"
    ws_headers = json.dumps({"Origin": "https://data.tradingview.com"})
    signin_headers = {"Referer": "https://www.tradingview.com"}
    ws_timeout = 5

    def __init__(
        self,
        username: str = None,
        password: str = None,
    ) -> None:
        """Create TvDatafeed object

        Args:
            username (str, optional): tradingview username. Defaults to None.
            password (str, optional): tradingview password. Defaults to None.
        """

        self.ws_debug = False

        self.token = self.auth(username, password)

        if self.token is None:
            self.token = "unauthorized_user_token"
            logger.warning(
                "you are using nologin method, data you access may be limited"
            )

        self.ws = None
        self.session = self.generate_session()
        self.chart_session = self.generate_chart_session()

    def auth(self, username, password):

        if username is None or password is None:
            token = None

        else:
            data = {"username": username, "password": password, "remember": "on"}
            try:
                response = requests.post(
                    url=self.sign_in_url, data=data, headers=self.signin_headers
                )
                token = response.json()["user"]["auth_token"]
            except Exception as e:
                logger.error(f"error during sign in: {e}")
                token = None

        return token

    def create_connection(self):
        logging.debug("creating websocket connection")
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket",
            headers=self.ws_headers,
            timeout=self.ws_timeout,
        )

    @staticmethod
    def filter_raw_message(text):
        try:
            found = re.search('"m":"(.+?)",', text).group(1)
            found2 = re.search('"p":(.+?"}"])}', text).group(1)

            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")

    @staticmethod
    def generate_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "qs_" + random_string

    @staticmethod
    def generate_chart_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "cs_" + random_string

    @staticmethod
    def prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def create_message(self, func, paramList):
        return self.prepend_header(self.construct_message(func, paramList))

    def send_message(self, func, args):
        m = self.create_message(func, args)
        if self.ws_debug:
            print(m)
        self.ws.send(m)

    @staticmethod
    def create_hist_df(raw_data, symbol):
        try:
            out = re.search('"s":\[(.+?)\}\]', raw_data).group(1)
            x = out.split(',{"')
            data = list()
            volume_data = True

            for xi in x:
                xi = re.split("\[|:|,|\]", xi)
                ts = datetime.datetime.fromtimestamp(float(xi[4]))

                row = [ts]

                for i in range(5, 10):

                    # skip converting volume data if does not exists
                    if not volume_data and i == 9:
                        row.append(0.0)
                        continue
                    try:
                        row.append(float(xi[i]))

                    except ValueError:
                        volume_data = False
                        row.append(0.0)
                        logger.debug("no volume data")

                data.append(row)

            data = pd.DataFrame(
                data, columns=["datetime", "open", "high", "low", "close", "volume"]
            ).set_index("datetime")
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")

    def parse_symbol_data(self, raw_data):
        results = raw_data.split("\n")
        for result in results:
            if symbol_resolved in result:
                input = result.replace('\\\\"', "")
                parsed_data = self.parse_m_format(input)

                for json_entry in parsed_data:
                    if "m" in json_entry:
                        if json_entry["m"] == symbol_resolved:
                            raw_data = json_entry["p"][2]
                            break

        return raw_data

    @staticmethod
    def format_symbol(symbol, exchange, contract: int = None):

        if ":" in symbol:
            pass
        elif contract is None:
            symbol = f"{exchange}:{symbol}"

        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"

        else:
            raise ValueError("not a valid contract")

        return symbol

    @staticmethod
    def parse_m_format(input_string):
        pattern = r"~m~(\d+)~m~"
        segments = re.split(pattern, input_string)
        result = []

        i = 1  # Start from the first number-length indicator
        while i < len(segments):
            try:
                length = int(segments[i])
                payload = segments[i + 1][:length]
                result.append(json.loads(payload))
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Error processing segment: {segments[i + 1]}")
            i += 2  # Move to the next number-length indicator

        return result

    def send_set_auth_token(self):
        self.send_message(set_auth_token_msg, [self.token])

    def send_chart_create_session_msg(self):
        self.send_message(chart_create_session_msg, [self.chart_session, ""])

    def send_quote_create_session_msg(self):
        self.send_message(quote_create_session_msg, [self.session])

    def send_quote_set_fields_overview_msg(self, fields=fields):
        fields.insert(0, self.session)
        self.send_message(quote_set_fields_msg, fields)

    def send_quote_add_symbols_msg(self, symbol):
        self.send_message(
            quote_add_symbols_msg,
            [self.session, symbol, {"flags": ["force_permission"]}],
        )

    def send_quote_fast_symbols_msg(self, symbol):
        self.send_message(quote_fast_symbols_msg, [self.session, symbol])

    def send_resolve_symbol_msg(self, symbol, extended_session: bool = False):
        self.send_message(
            resolve_symbol_msg,
            [
                self.chart_session,
                "symbol_1",
                '={"symbol":"'
                + symbol
                + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"')
                + "}",
            ],
        )

    def send_create_series_msg(self, interval, n_bars):
        self.send_message(
            create_series_msg,
            [self.chart_session, "s1", "s1", "symbol_1", interval, n_bars],
        )

    def send_switch_timezone_msg(self):
        self.send_message(switch_timezone_msg, [self.chart_session, "exchange"])

    def receive_data(self, sentinel):
        raw_data = ""
        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except Exception as e:
                logger.error(e)
                break

            if sentinel in result:
                break

        return raw_data

    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        n_bars: int = 10,
        fut_contract: int = None,
        extended_session: bool = False,
    ) -> pd.DataFrame:
        """get historical data

        Args:
            symbol (str): symbol name
            exchange (str, optional): exchange, not required if symbol is in format EXCHANGE:SYMBOL. Defaults to None.
            interval (str, optional): chart interval. Defaults to 'D'.
            n_bars (int, optional): no of bars to download, max 5000. Defaults to 10.
            fut_contract (int, optional): None for cash, 1 for continuous current contract in front, 2 for continuous next contract in front . Defaults to None.
            extended_session (bool, optional): regular session if False, extended session if True, Defaults to False.

        Returns:
            pd.Dataframe: dataframe with sohlcv as columns
        """
        symbol = self.format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )
        logger.debug(f"getting data for {symbol}...")

        interval = interval.value

        self.create_connection()

        self.send_set_auth_token()
        self.send_chart_create_session_msg()
        self.send_quote_create_session_msg()
        self.send_quote_set_fields_overview_msg()
        self.send_quote_add_symbols_msg(symbol)
        self.send_resolve_symbol_msg(symbol, extended_session)
        self.send_create_series_msg(interval, n_bars)

        raw_data = self.receive_data(sentinel=series_completed)

        return self.create_hist_df(raw_data, symbol)

    def get_symbol_data(
        self,
        symbol: str,
        exchange: str = "NSE",
        fut_contract: int = None,
        extended_session: bool = False,
    ) -> dict:
        """get symbol data

        Args:
            symbol (str): symbol name
            exchange (str, optional): exchange, not required if symbol is in format EXCHANGE:SYMBOL. Defaults to None.
            fut_contract (int, optional): None for cash, 1 for continuous current contract in front, 2 for continuous next contract in front . Defaults to None.
            extended_session (bool, optional): regular session if False, extended session if True, Defaults to False.

        Returns:
            dict
        """
        symbol = self.format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )

        self.create_connection()
        self.send_set_auth_token()
        self.send_chart_create_session_msg()
        self.send_resolve_symbol_msg(symbol, extended_session)

        logger.debug(f"getting data for {symbol}...")

        raw_data = self.receive_data(sentinel=symbol_resolved)

        return self.parse_symbol_data(raw_data)

    def search_symbol(self, text: str, exchange: str = ""):
        url = self.search_url.format(text, exchange)

        symbols_list = []
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Host": "symbol-search.tradingview.com",
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Referer": "https://www.tradingview.com/",
                "Origin": "https://www.tradingview.com",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Priority": "u=4",
                "TE": "trailers",
            }
            resp = requests.get(url, headers=headers)

            symbols_list = json.loads(
                resp.text.replace("</em>", "").replace("<em>", "")
            )
        except Exception as e:
            logger.error(e)

        return symbols_list

    def get_symbol_ratios(self, text: str, exchange: str = ""):
        # ~m~36~m~{"m":"set_data_quality","p":["low"]}
        # ~m~54~m~{"m":"set_auth_token","p":["unauthorized_user_token"]}
        # ~m~34~m~{"m":"set_locale","p":["en","US"]}
        # ~m~52~m~{"m":"quote_create_session","p":["qs_7tsehQTQnh0k"]}
        # ~m~60~m~{"m":"quote_add_symbols","p":["qs_7tsehQTQnh0k","LSE:GENL"]}
        # ~m~61~m~{"m":"quote_fast_symbols","p":["qs_7tsehQTQnh0k","LSE:GENL"]}
        # ~m~52~m~{"m":"quote_create_session","p":["qs_EQpcT7Ixjgiu"]}
        # ~m~473~m~{"m":"quote_set_fields","p":["qs_EQpcT7Ixjgiu","base-currency-logoid","ch","chp","currency-logoid","currency_code","currency_id","base_currency_id","current_session","description","exchange","format","fractional","is_tradable","language","local_description","listed_exchange","logoid","lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","typespecs","update_mode","volume","variable_tick_size","value_unit_id","unit_id","measure"]}
        # ~m~60~m~{"m":"quote_add_symbols","p":["qs_EQpcT7Ixjgiu","LSE:GENL"]}
        # ~m~61~m~{"m":"quote_fast_symbols","p":["qs_EQpcT7Ixjgiu","LSE:GENL"]}
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tv = TvDatafeed()
    # print(tv.get_hist("CRUDEOIL", "MCX", fut_contract=1))
    # print(tv.get_hist("NIFTY", "NSE", fut_contract=1))
    # print(
    #     tv.get_hist(
    #         "EICHERMOT",
    #         "NSE",
    #         interval=Interval.in_1_hour,
    #         n_bars=500,
    #         extended_session=False,
    #     )
    # )

    print(tv.get_hist("GAZP", "MOEX"))
    sym_data = tv.get_symbol_data("GAZP", "MOEX")
    print(json.dumps(sym_data, indent=4))
