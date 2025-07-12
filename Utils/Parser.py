import asyncio
import random
import pandas
from selenium.webdriver.chrome.options import Options
import time
import os
from bs4 import BeautifulSoup
import requests
from Utils import get_last_string, append_dataframe_to_table
from config import TXT_FILES_DIR
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

def init_driver():
    try:
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        driver = uc.Chrome(headless=False, version_main=138)
        return driver
    except Exception as e:
        print(f"Ошибка инициализации драйвера: {e}")
        raise

def human_like_delay():
    time.sleep(random.uniform(1, 3))

def SaveSrc(path: str, url: str):
    driver = None
    try:
        driver = init_driver()
        driver.get(url)
        time.sleep(3)
        end = 40
        for scroll in range(1, end+1):
            time.sleep(random.randrange(20, 40))
            if "mangalib" not in driver.title.lower():
                raise Exception("Страница не загрузилась корректно")
            driver.execute_script("window.scrollBy(0, 2000);")

            html = driver.page_source
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Страница успешно сохранена в {path}")
    except Exception as e:
        print(f"Ошибка при сохранении страницы: {e}")
    finally:
        if driver:
            driver.quit()

def Load_Info_Title(count_lines: int):
    try:
        titles = []
        for i in range(1, count_lines):
            with open(f"DataBase/Slot_{i}/Title.txt", "r", encoding="utf-8") as file:
                titles.append(file.read())
        return titles
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")


def Save_Info(PathSrc:str):
    with open(f"{PathSrc}", "r", encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    elements = soup.find_all(class_="cover__img")
    counter = 1
    for element in elements:
        os.makedirs(f"DataBase/Slot_{counter}", exist_ok=True)
        Title = element.get("alt").replace("читать онлайн", "")
        src = element.get("src")
        with open(f"DataBase/Slot_{counter}/Title.txt", "w", encoding="utf-8") as file:
            file.write(Title)
        with open(f"DataBase/Slot_{counter}/src.jpg", "wb") as file:
            file.write(requests.get(src).content)
        counter += 1

async def Get_package_part(PathSrc:str, counterMAX:int)->dict:
    """
    Функция для получения базовой информации о произведениях из каталога, 1 часть пакета

    :param PathSrc: Путь к HTML коду страницы каталога
    :param counterMAX: Сколько произведений нужно добавить в пакет
    """
    with open(f"{PathSrc}", "r", encoding="utf-8") as file:
        src = file.read()
    flag_parsing1 = False
    flag_parsing2 = False
    counter = 0
    last_string = await get_last_string()
    soup = BeautifulSoup(src, "lxml")
    elements = soup.find_all(class_="cover__img")
    titles = list()
    srcs = list()
    links = list()
    for element in elements:
        title = element.get("alt").replace("читать онлайн", "")
        src = element.get("src")
        if flag_parsing1:
            titles.append(title)
            srcs.append(src)
            counter += 1
            if counter == counterMAX:
                break
        if not flag_parsing1:
            if last_string['title'] != '---':
                if title == last_string['title'] and src == last_string['src']:
                    flag_parsing1 = True
            else:
                flag_parsing1 = True
                titles.append(title)
                srcs.append(src)
                counter += 1
    counter = 0
    elements = soup.find_all("a", class_="cover _shadow")
    for element in elements:
        link = f'https://mangalib.me{element.get("href")}'.replace("?from=catalog", "")
        if flag_parsing2:
            links.append(link)
            counter += 1
            if counter == counterMAX:
                break
        if not flag_parsing2:
            if last_string['title'] != '---':
                if link == last_string['link']:
                    flag_parsing2 = True
            else:
                flag_parsing2 = True
                links.append(link)
                counter += 1
    return {
        "title": titles,
        "src": srcs,
        "link": links,
    }

async def Get_Package(package_part:dict)->dict:
    """
    Функция, которая завершает пакет, добавляет описание произведений

    :param package_part: 1 часть пакета
    :return:
    """
    driver = init_driver()
    captions = list()
    for link in package_part["link"]:
        try:
            human_like_delay()
            driver.get(link)
            time.sleep(2)
            for _ in range(10):
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ub_am"))
                    )
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    caption_div = soup.find("div", class_="ub_am")
                    if caption_div:
                        caption = caption_div.get_text(strip=True)
                        captions.append(caption.replace('&quot;', ""))
                        print(f"Успешно: {caption[:50]}...")
                        break
                except Exception as e:
                    print(f"Ошибка при обработке {link}: {e}")
            else:
                captions.append("")
                print(f"Не удалось получить описание для {link}")
        except Exception as e:
            print(f"Критическая ошибка для {link}: {e}")
    driver.quit()
    package = {
        "title": package_part["title"], # Название
        "src": package_part["src"], # Ссылка на изображение
        "link": package_part["link"], # Ссылка на произведение
        "caption": captions # Описание произведения
    }
    return package

async def Activate_Parsing(counterMAX):
    """
    Функция активации подгрузки пакетов в базу данных

    :param counterMAX: количество произведений, которые мы помещаем в пакет
    :return:
    """
    package_part = await Get_package_part(TXT_FILES_DIR / "Page_1.txt", counterMAX=counterMAX)
    package = await Get_Package(package_part)
    await append_dataframe_to_table(pandas.DataFrame(package))

#SaveSrc(TXT_FILES_DIR / "Page_1.txt",'https://mangalib.me/ru/catalog?seed=939bc44b67e882cd5db8953407dd601d')

if __name__ == '__main__':
    for _ in range(15):
        asyncio.run(Activate_Parsing(10))
        time.sleep(random.randrange(40, 60))