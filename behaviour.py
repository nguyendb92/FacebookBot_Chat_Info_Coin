# -*- coding: utf-8 -*-
# !/user/bin/env python3

import requests
import re


API_QUERY_URL = "https://api.coinmarketcap.com/v1/ticker/{}/?convert={}"

REGEXES = [re.compile(r'([a-z]+)\sprice\s\vs\s([a-z]+).*'),
           re.compile(r'([a-z]+)\sprice\sin\s([a-z]+).*'),
           re.compile(r'([a-z]+)\sprice\sversus\s([a-z]+).*'),
           re.compile(r'([a-z]+)\sprice\sagainst\s([a-z]+).*'),
           re.compile(r'price\sof\s([a-z]+)\svs\s([a-z]+).*'),
           re.compile(r'price\sof\s([a-z]+)\svernsus\s([a-z]+).*'),
           re.compile(r'price\sof\s([a-z]+)\sin\s([a-z]+).*'),
           re.compile(r'price\sof\s([a-z]+)\sinagainst\s([a-z]+).*'),
           ]

FULL_STRING_REGEXS = [
    re.compile(r'^([a-z]+)$'),
    re.compile(r'^([a-z]+)\sprice$'),
    re.compile(r'^price of ([a-z]+)$'),
    re.compile(r'([a-z]+)/([a-z]+)$'),
    re.compile(r'([a-z]+)-([a-z]+)$'),
    re.compile(r'([a-z]+)\sin\s([a-z]+)$'),
    re.compile(r'([a-z]+)\svs\s([a-z]+)$'),
    re.compile(r'([a-z]+)\sversus\s([a-z]+)$'),
    re.compile(r'([a-z]+)\sagainst\s([a-z]+)$'),
    ]

KNOWN_CONVERSION_CURRENCIES = [
    "aud",
    "brl",
    "cad",
    "chf",
    "clp",
    "cny",
    "czk",
    "dkk",
    "eur",
    "gbp",
    "hkd",
    "huf",
    "idr",
    "ils",
    "inr",
    "jpy",
    "krw",
    "mxn",
    "myr",
    "nok",
    "nzd",
    "php",
    "pkr",
    "pln",
    "rub",
    "sek",
    "sgd",
    "thb",
    "try",
    "twd",
    "usd",
    "zar"
]


def understand_coin_and_conversion_currency(message_text):
    # làm sạch tin nhắn, và xóa khoảng trắng
    message_text = message_text.lstrip().rstrip().replace("?", "")
    # xóa các khoảng trắng thừa > 1 space trong tin nhắn
    message_text = " ".join(message_text.split())
    # chuyển các chữ in hoa thành chữ thường
    message_text = message_text.lower()
    # tìm các word cần lấy
    coin_name = None
    conversion_currency = None
    for r in REGEXES:
        # lặp qua từng phần tử  trong list REGEXS
        matches = r.search(message_text)
        if matches is not None:
            g1 = matches.group(1)
            g2 = matches.group(2)
            #  nếu mà g1 tìm kiếm thấy và gán giá chị cho coin_name = g1
            if g1 is not None:
                coin_name = g1
            # tương tự
            if g2 is not None:
                conversion_currency = g2
            # khi ta có cả hai
            if g1 is not None and g2 is not None:
                return coin_name, conversion_currency

    for r in FULL_STRING_REGEXS:
        matches = r.search(message_text)
        if matches is not None:
            g1 = matches.group(1)
            try:
                g2 = matches.group(2)
            except IndexError:
                g2 = None
            if g1 is not None:
                coin_name = g1
            if g2 is not None:
                conversion_currency = g2
            if g1 is not None and g2 is not None:
                return coin_name, conversion_currency
    # chúng ta đã có 2 thứ cần thiết
    return coin_name, conversion_currency


# để kiểm trả xem mã tiền có trong danh sách hiện có không
def is_conversion_currency_supported(conversion_currency):
    # trả về giá trị là boolean
    return conversion_currency.lower() in KNOWN_CONVERSION_CURRENCIES


def fetch_cryptocurrency_data(coin_name, conversion_currency):
    assert coin_name is not None
    assert conversion_currency is not None
    url = API_QUERY_URL.format(coin_name, conversion_currency)
    price_key = 'price_{}'.format(conversion_currency.lower())
    response = requests.get(url)
    if response.status_code == 404:
        raise ValueError()
    if response.status_code != requests.codes.ok:
        raise IOError()
    coin = response.json()[0]
    price = coin.get(price_key, None)
    percent_change_24h = coin.get('percent_change_24h', None)
    return price, percent_change_24h


def answer(message_text):
    """ nhận đầu vào là một tin nhắn và trả lời một cách tự nhiên
    :parma: message_text
    :return: str
    """
    coin_name, conversion_currency = understand_coin_and_conversion_currency(message_text)
    # nếu không có tên coin trong danh sách
    if coin_name is None:
        return "Sorry I don't know that crypto. Can you specify it by full name?"
    # kiểm tra xem tiền đang được hỗ trợ
    if conversion_currency is None:
        conversion_currency = "usd"
    else:
        if not is_conversion_currency_supported(conversion_currency):
            return "I don't understand your own currency. can you specify it by symbol?"

    # fetch data
    try:
        price, percent_change_24h = fetch_cryptocurrency_data(coin_name, conversion_currency)
    except ValueError:
        return "Sorry looks like your cryto does not exist. Did you type it correctly?"
    except IOError:
        return "Sorry my source of crypto prices is unavailable at the \
                 moment. please try again in a while"

    # chuan bi cau tra loi ve tien
    if price is None:
        return "Sorry I was unable to find the price. Please try again in a while"
    else:
        answer_text = "Current price for {} is {} {}".format(
            coin_name.title(),
            price,
            conversion_currency.upper()
        )

    # them thong tin phan tram thay doi
    if percent_change_24h is not None:
        change = float(percent_change_24h)
        if change < 0.0:
            answer_text += ", with a loss of {}% in the last 24 hours".format(abs(change))
        elif change > 0.0:
            answer_text += ", with a gain of {}% in the last 24 hours".format(change)
        else:
            answer_text += ', unchanged in the last 24 hours'
    return answer_text
