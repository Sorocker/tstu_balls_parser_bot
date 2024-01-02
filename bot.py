import asyncio
from arsenic import get_session, keys, browsers, services
import logging
from aiogram.types import FSInputFile
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
)
from bs4 import BeautifulSoup
import tkinter as tk
import random
import os
import getpass

# Хранение данных о запросах команды, для антифлуда
last_start_command = {}

# Создание объекта роутера
form_router = Router()

# Получение размера экрана для разворачивания окна браузера, для наглядности
root = tk.Tk()
mon_width = root.winfo_screenwidth()
mon_height = root.winfo_screenheight()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
TOKEN = 'BOT_TOKEN'
bot = Bot(token=TOKEN)

# Диспетчер + роутер
dp = Dispatcher()
dp.include_router(form_router)

# Переменные для подключения к сайту
APP_PASSW = "APP_PASSW"
USER_NAME = 'USER_NAME'
USER_PASSWORD = 'USER_PASSWORD'
RATE_LIMIT = 80
group_id = "6159"
group_link = ""
balls_page = "::P41_GROUP_ID:"
session_id = ""
ft_page = ""
start_of_link = "http://web-iais.admin.tstu.ru:7777/zion/"


def check_password(password):
    return password == APP_PASSW


# Оформление файла отправки (верхняя часть)
html_design_1 = """
<html>

<head>
<style>
table {
  border-collapse: collapse;
  width: 100%;
}

table, th, td {
  border: 1px solid black;
}

th, td {
  text-align: left;
  padding: 8px;
}
</style>
</head>
<body>
"""


async def click_link(time_to_sleep, your_ses, link_text='', for_search='', click_all=False, chat_id: int = 0,
                     last_name=''):
    await asyncio.sleep(time_to_sleep)
    global ft_page
    html_design_2 = """
    <script>
       var tables = document.getElementsByTagName('table');
    for (var t = 0; t < tables.length; t++) {
      var rows = tables[t].getElementsByTagName('tr');
      for (var i = 1; i < rows.length; i++) {
        var text = rows[i].getElementsByTagName('td')[0].innerHTML;
        if (text.toLowerCase().startsWith('фамилия')) {
          rows[i].style.backgroundColor = 'yellow';
        }
      }
    }
    </script>
    </body>
    </html>
    """
    html_design_2 = html_design_2.replace('фамилия', last_name.lower())
    elements = await your_ses.get_elements('a')
    print("elements: " + str(elements.__len__()))
    links = [await e.get_attribute('href') for e in elements]
    i = 0
    file_name = ''
    if click_all:
        file_name = f"req_{random.randint(1, 1000)}.html"
        with open(file_name, 'w') as file:
            file.write(html_design_1)
    for l in links:
        l_text = str(l)
        # print("!!!!!!!!!!!!LINKS:!!!!!!!!!" + l_text)
        if not for_search:
            if l_text == link_text:
                await elements[i].click()
                break
        else:
            if not click_all:
                if l_text.__contains__(for_search):
                    ft_page = start_of_link + l_text
                    print("~!~~!~~~~~!~~!~~~~~!~~~~~!~~~~~~!~~~~~~~~!~~" + ft_page)
                    await elements[i].click()
                    break
            else:
                if l_text.__contains__(for_search):
                    await your_ses.execute_script("window.open('" + start_of_link + l_text + "', '_blank');")
                    await your_ses.get(start_of_link + l_text)
                    page_source = await your_ses.get_page_source()

                    soup = BeautifulSoup(page_source, 'html.parser')
                    discipline = soup.find('span', {"id": "P42_DISC"})
                    print('<h1>' + discipline.text + '</h1>' + '<table>')

                    with open(file_name, 'a') as file:
                        file.write('<h1>' + discipline.text + '</h1>' + '<table>')

                    all_tr = soup.find_all('tr')
                    for tr in all_tr[2:]:
                        print(tr)
                        with open(file_name, 'a') as file:
                            file.write(str(tr))

                    with open(file_name, 'a') as file:
                        file.write('</table>')
        i += 1
    if click_all:
        with open(file_name, 'a') as file:
            file.write(html_design_2)
        for_send = FSInputFile(file_name)
        await bot.send_document(chat_id, for_send)
        os.remove(file_name)


async def balls_request(chat_id: int = 0, last_name=''):
    service = services.Geckodriver()
    browser = browsers.Firefox()
    async with get_session(service, browser) as session:
        await session.get('http://web-iais.admin.tstu.ru:7777/zion/f?p=503:LOGIN_DESKTOP')
        await session.set_window_size(mon_width, mon_height)
        uname = await session.wait_for_element(5, 'input[name="p_t01"]')
        upass = await session.wait_for_element(5, 'input[name="p_t02"]')
        await uname.send_keys(USER_NAME)
        await upass.send_keys(USER_PASSWORD)
        await upass.send_keys(keys.ENTER)
        await click_link(5, session, link_text="javascript:apex.submit('T_ЗАНЯТИЯ/ОЦЕНКИ');")
        await click_link(5, session, for_search=balls_page + group_id)
        await click_link(5, session, for_search=",1,20", click_all=True, chat_id=chat_id, last_name=last_name)


class Form(StatesGroup):
    l_name = State()


@form_router.message(Command("start"))
async def command_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if user_id in last_start_command:
        if (message.date - last_start_command[user_id]).seconds < RATE_LIMIT:
            await message.answer("Будь терпеливее...")
            return
    last_start_command[user_id] = message.date
    await message.answer("Сессия начата")

    await state.set_state(Form.l_name)
    await message.answer(
        "Назови фамилию",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Form.l_name)
async def process_name(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Подожди pls минуту, я пришлю файл, открой его браузером...",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.update_data(name=message.text)
    await balls_request(chat_id=message.chat.id, last_name=message.text)


# Запуск процесса пуллинга новых апдейтов
async def main():
    password = getpass.getpass("Введите пароль: ")

    if check_password(password):
        print("Пароль правильный. Приложение запущено.")
    else:
        print("Неправильный пароль. Попробуйте еще раз.")
        return
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
