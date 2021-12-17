#!/usr/bin/env python

import argparse
import os

from Bot import Bot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='')
    args = parser.parse_args()

    token = args.token
    if not token:
        if not "TELEGRAM_TOKEN" in os.environ:
            print(
                "Please, set bot token through --token or TELEGRAM_TOKEN env variable"
            )
            return
        token = os.environ["TELEGRAM_TOKEN"]

    bot = Bot(token)
    bot.main_loop()


if __name__ == "__main__":
    main()
