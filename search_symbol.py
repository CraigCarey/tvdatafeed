#! /usr/bin/env python3

from tvDatafeed import TvDatafeed

from pprint import pprint


# get credentials for tradingview
def read_username_and_password(file_path):
    try:
        with open(file_path + "_user", "r") as file:
            username = file.read().strip()

        with open(file_path + "_pass", "r") as file:
            password = file.read().strip()

        return username, password

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def main():
    username, password = read_username_and_password("/home/craigc/.keys/tradingview")

    # initialize tradingview
    tv = TvDatafeed(username=username, password=password)

    symbols = tv.search_symbol("BBG000DKRVS2")

    pprint(symbols)


if __name__ == "__main__":
    main()
