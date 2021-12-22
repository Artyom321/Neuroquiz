#!/usr/bin/env python

import argparse
import os

from Bot import Bot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='')
    parser.add_argument('--ignore', action='store_true')
    args = parser.parse_args()

    token = args.token
    if not token:
        if not "TELEGRAM_TOKEN" in os.environ:
            print(
                "Please, set bot token through --token or TELEGRAM_TOKEN env variable"
            )
            return
        token = os.environ["TELEGRAM_TOKEN"]

    ignore_previous_updates = False
    if args.ignore:
        ignore_previous_updates = True

    bot = Bot(token, ignore_previous_updates=ignore_previous_updates)
    bot.main_loop()


if __name__ == "__main__":
    main()
