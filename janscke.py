import os
import json
import time
import collections

import requests

from getpass import getpass

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

reloads_in_browser = 100

extensions = {
    "agda": ".agda",
    "brainfuck": ".bf",
    "c": ".c",
    "cfml": ".cfm",
    "clojure": ".clj",
    "cobol": ".cbl",
    "coffeescript": ".coffee",
    "commonlisp": ".lisp",
    "coq": ".coq",
    "c++": ".cpp",
    "crystal": ".cr",
    "c#": ".cs",
    "d": ".d",
    "dart": ".dart",
    "elixir": ".exs",
    "erlang": ".erl",
    "factor": ".factor",
    "forth": ".4th",
    "fortran": ".f",
    "f#": ".fs",
    "go": ".go",
    "groovy": ".groovy",
    "haskell": ".hs",
    "haxe": ".hx",
    "idris": ".idr",
    "java": ".java",
    "javascript": ".js",
    "julia": ".jl",
    "kotlin": ".kt",
    "lua": ".lua",
    "nasm": ".asm",
    "nim": ".nim",
    "objective-c": ".m",
    "ocaml": ".ml",
    "pascal": ".p",
    "perl": ".pl",
    "php": ".php",
    "powershell": ".ps1",
    "prolog": ".pl",
    "purescript": ".purs",
    "python": ".py",
    "r": ".r",
    "racket": ".rkt",
    "raku": ".raku",
    "riscv": ".o",
    "ruby": ".rb",
    "rust": ".rs",
    "scala": ".scala",
    "shell": ".sh",
    "solidity": ".sol",
    "sql": ".sql",
    "swift": ".swift",
    "typescript": ".ts",
    "vb": ".vb",
}


class CodeWarsApi:
    def __init__(self):
        pass

    def get_kata_name_and_description(self, kata_id):
        endpoint = f"https://www.codewars.com/api/v1/code-challenges/{kata_id}"
        res = requests.get(endpoint)
        data = json.loads(res.text)
        return data["name"], data["description"]

    def get_user_total_completed(self, user_name, page_number):
        endpoint = f"https://www.codewars.com/api/v1/users/{user_name}/code-challenges/completed?page={page_number}"

        res = requests.get(endpoint)
        return json.loads(res.text)


class Kata:
    def __init__(self, soup):
        self.soup = soup

    @property
    def source_codes(self):
        codes = self.soup.find_all("div", {"class": "markdown"})
        return ["".join(code.findAll(string=True)) for code in codes]

    @property
    def languages(self):
        languages = self.soup.find_all("h6")
        return [language.text.rstrip(":").lower() for language in languages]

    @property
    def difficulty(self):
        difficulty = self.soup.find("div", {"class": "item-title"}).find("span").text
        return difficulty.replace(" ", "-").lower()

    @property
    def title(self):
        title = self.soup.find("div", {"class": "item-title"}).find("a").text
        return title.replace(" ", "-").lower()

    @property
    def kata_id(self):
        href = self.soup.find("div", {"class": "item-title"}).find("a")["href"]
        return href.split("/")[-1]


class KataParser:
    def __init__(self, html):
        soup = BeautifulSoup(html, "html.parser")
        self.elems = soup.find_all("div", {"class": "list-item-solutions"})

    def parse_katas(self):
        return [Kata(elem) for elem in self.elems]


def trimPath(value):
    for c in r'\/:.!*?"<>|î»':
        value = value.replace(c, "")
    while "--" in value:
        value = value.replace("--", "-")
    if value[-1] == "-":
        value = value[:-1]
    return value.strip()


def get_source(codewars_email, codewars_password):
    options = webdriver.ChromeOptions()
    # options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.codewars.com/users/sign_in")

    usernameElem = driver.find_element(By.ID, "user_email")
    passwordElem = driver.find_element(By.ID, "user_password")

    usernameElem.send_keys(codewars_email)
    passwordElem.send_keys(codewars_password)

    driver.find_element(By.XPATH, "//button[2]").click()
    driver.find_element(
        By.XPATH, """//*[@id="header_profile_link"]/div[1]/img"""
    ).click()

    user_name = driver.current_url.split("/")[-1]
    api = CodeWarsApi()

    completed_katas = 0
    total_pages = 1
    current_page = 0
    while current_page < total_pages:
        data = api.get_user_total_completed(user_name, current_page)
        total_pages = data["totalPages"]
        current_page += 1
        for i in data["data"]:
            completed_katas += len(i["completedLanguages"])

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Solutions"))
    )
    driver.find_element(By.LINK_TEXT, "Solutions").click()

    calculated_max_refreshes = completed_katas // 15 + 3
    if calculated_max_refreshes < reloads_in_browser:
        nReloads = calculated_max_refreshes
    else:
        nReloads = reloads_in_browser

    for _ in range(nReloads):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    out = driver.page_source

    driver.close()

    return out


def generate_tree(source, base_dir, want_html):
    collections.Callable = collections.abc.Callable
    parser = KataParser(source)
    katas = parser.parse_katas()
    katas_len = len(katas)
    api = CodeWarsApi()
    print("Exporting katas...")

    for i, kata in enumerate(katas):
        print("\r{}/{} katas exported.".format(i + 1, katas_len), end="")
        kata_info = ""
        while not kata_info:
            try:
                kata_info = api.get_kata_name_and_description(kata.kata_id)
            except json.decoder.JSONDecodeError:
                print(
                    f"\r{i+1}/{katas_len} katas exported. Trouble connecting to the codewars API (Kata ID: {kata.kata_id}). Retrying..."
                )
                kata_info = ""
        kata_name = kata_info[0]
        kata_description = kata_info[1]

        for language, source_code in zip(kata.languages, kata.source_codes):
            file_dir = os.path.join(
                base_dir, kata.difficulty, trimPath(kata.title), language
            )
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            filename = "solution" + extensions.get(language, "")
            with open(os.path.join(file_dir, filename), "w", encoding="utf-8") as fout:
                fout.write(source_code)
            with open(
                os.path.join(file_dir, "README.md"), "w", encoding="utf-8"
            ) as fout:
                fout.write(
                    f"# [{kata_name}](https://www.codewars.com/kata/{kata.kata_id})\n\n"
                )
                fout.write(kata_description)
    
    if want_html:
        with open(f"{base_dir}/solutions.html", "w", encoding="utf-8") as file:
            file.write(source)


if __name__ == "__main__":
    print("Welcome to jans-codewars-kata-exporter!")
    codewars_email = input("Please enter your codewars account e-mail adress: ")
    codewars_password = getpass(
        "Please enter your codewars password (reset password if you used a github account): "
    )
    want_html = input("Do you want the HTML file of your solutions [y/N]: ")
    if not want_html or want_html.lower().startswith("n"):
        want_html = False
    else:
        want_html = True
    download_folder = input("Enter a path to save your files [./solutions]: ")
    if not download_folder:
        download_folder = "./solutions"
    print("janscke will now open a Chrome window to get your kata solutions.")
    time.sleep(3)
    try:
        source = get_source(codewars_email, codewars_password)
    except NoSuchElementException:
        print("Error while fetching the data. Maybe mistyped user credentials? Exiting.")
        exit()
    print("Finished getting your kata solutions.\nStarting export.")
    generate_tree(source, download_folder, want_html)
