from telebot import types


async def Create_Button_From_Message(bot, message, message_text: str, text_callback: dict):
    """
    Создает сообщение с кнопками

    :param bot: экземпляр асинхронного бота (AsyncTeleBot)
    :param message: message = message
    :param message_text: текст сообщения, к которому создаются кнопки
    :param text_callback: словарь формата {текст: callback_data}
    """
    markup = types.InlineKeyboardMarkup()
    for text, callback in text_callback.items():
        markup.add(types.InlineKeyboardButton(text=text, callback_data=callback))
    await bot.send_message(
        message.chat.id,
        message_text,
        reply_markup=markup
    )


async def Create_Button_From_Message_With_Photo(bot,
                                                message,
                                                photo_caption: str,
                                                text_callback: dict,
                                                photo_url: str,
                                                markup = None):
    """
        Создает сообщение с кнопками

        :param bot: экземпляр асинхронного бота (AsyncTeleBot)
        :param message: message = message
        :param photo_caption: текст сообщения, к которому создаются кнопки
        :param text_callback: словарь формата {текст: callback_data}
        :param photo_url: ссылка на фото
        """
    if markup == None:
        markup = types.InlineKeyboardMarkup()
    else:
        markup = markup
    for text, callback in text_callback.items():
        markup.add(types.InlineKeyboardButton(text=text, callback_data=callback))
    await bot.send_photo(
        message.chat.id,
        caption=photo_caption,
        reply_markup=markup,
        photo=photo_url
    )