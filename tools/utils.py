from io import BytesIO
from json import load, dump


def get_config(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as file:
        data: dict = load(file)
    return data


def save_config(filename: str, data: dict) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        dump(data, file, indent=4, ensure_ascii=False)


def is_link(value: str) -> bool:
    if not value.startswith("https://"):
        return False

    if "instagram.com" not in value:
        raise KeyError

    return True


def str2file(text: str, filename: str) -> BytesIO:
    file = BytesIO(text.encode())
    file.name = filename
    file.seek(0)
    return file


def username_from_link(value: str) -> str:
    alph = "abcdefghijklmnopqrstuvwxyz"
    nums = "1234567890"
    symbols = "_,."
    res = alph + nums + symbols

    try:
        if not is_link(value):

            if value.startswith("@"):
                return value.split("@")[-1]

            return value
    except KeyError:
        return False

    items = [item for item in value.split("/") if item]

    if len(items) != 3:
        return False

    username = items[-1]
    result = ""
    for letter in username:
        if letter not in res:
            break
        result += letter
    else:
        result = username

    return result
