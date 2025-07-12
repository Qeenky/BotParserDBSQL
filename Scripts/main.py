# Imports
from Token import token
from Utils import Create_Button_From_Message, Create_Button_From_Message_With_Photo, TextStart, TextMenu, get_data
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types

# Global Values
bot = AsyncTeleBot(token)

# Handlers
@bot.message_handler(commands=['start'])
async def start(message):
    await Create_Button_From_Message(bot=bot,
                            message=message,
                            message_text=TextStart,
                            text_callback={"Меню":"Menu"}
                            )

@bot.callback_query_handler(func=lambda callback: True)
async def callback_handler(callback):
    try:
        if callback.data == "Menu":
            await Create_Button_From_Message(
                bot=bot,
                message=callback.message,
                message_text=TextMenu,
                text_callback={"Случайный тайтл": "Random_Title"}
            )
        elif callback.data == "Random_Title":
            Title = await get_data()
            Random_Title = Title.sample().squeeze()
            Caption = Random_Title['caption']
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Перейти на сайт", url=Random_Title['link']))
            if Caption in [None, ""]:
                Caption = "На сайте"
            if len(Caption) > 824:
                Caption = Caption[:820] + "..."
                print(Random_Title['title'])
            await Create_Button_From_Message_With_Photo(
                bot=bot,
                message=callback.message,
                photo_caption=f"{Random_Title['title']}\n\nОписание: {Caption}",
                photo_url=Random_Title['src'],
                text_callback={"Следующий тайтл": "Random_Title"},
                markup=markup
            )
    except Exception as e:
        print(f"Error: {e}")
        await bot.send_message(callback.message.chat.id, "⚠️ Произошла ошибка")


async def main():
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    asyncio.run(main())