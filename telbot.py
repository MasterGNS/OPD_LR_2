import json
import random
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
def bot():
    with open("token.txt", 'r', encoding='utf-8') as f:
        TOKEN = f.readline()
    # имя файла с вопросами и ответами
    JSON_FILE = 'questions.json'

    # парсим файл с вопросами и ответами
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    global score, current_question_index, num_questions, prevId
    score = 0
    current_question_index = 0
    prevId = []
    num_questions = len(questions)

    def test(id):
        global num_questions
        if id in prevId:
            random_index = random.randint(0, num_questions - 1)
            return test(random_index)
        else:
            return id

    # создаем бота
    bot = Bot(TOKEN)
    dp = Dispatcher(bot)

    # обработчик команды /start
    @dp.message_handler(commands=['start'])
    async def start(message: types.Message):
        await message.answer('Привет! Это бот викторина. Чтобы начать, набери команду /quiz.')

    @dp.message_handler(commands=['exit'])
    async def exit(message: types.Message):
        user_id = message.from_user.id
        user_file = f'user_{user_id}.json'
        if os.path.exists(user_file):
            with open(user_file, 'r') as f:
                data = json.load(f)
                score = data.get('score', 0)
            with open(user_file, 'w') as f:
                json.dump({'messages': [], 'score': score}, f)
            await message.answer(f'Вы вышли из игры. Ваш счет: {score}')
        else:
            await message.answer('Вы не начинали игру. Для начала наберите команду /quiz.')

    # обработчик команды /quiz
    @dp.message_handler(commands=['quiz'])
    async def quiz(message: types.Message):
        global right_answer, prevId
        random_index = random.randint(0, num_questions - 1)
        id = questions[random_index]["id"]
        random_index = test(id)
        prevId.append(random_index)
        right_answer = questions[random_index]['answer']
        question_text = questions[random_index]['question']
        answers = questions[random_index]['options']
        # создаем кнопки для ответов
        keyboard = types.InlineKeyboardMarkup()
        for answer in answers:
            keyboard.add(types.InlineKeyboardButton(text=answer, callback_data=answer))

        # отправляем вопрос пользователю
        await message.answer(question_text, reply_markup=keyboard)

    # обработчик нажатия на кнопку с ответом
    @dp.callback_query_handler(lambda c: True)
    async def process_callback_answer(callback_query: types.CallbackQuery):
        answer_text = callback_query.data
        global score, current_question_index

        if answer_text == right_answer:
            response_text = 'Правильно!'
            score += 100
            current_question_index += 1
        else:
            response_text = f'Неправильно! Правильный ответ: {right_answer}.'
            score = 0
            current_question_index = 0

        # сохраняем историю сообщений и количество очков пользователя в json файл
        user_id = callback_query.from_user.id
        user_file = f'user_{user_id}.json'
        with open(user_file, 'w') as f:
            json.dump({'messages': [callback_query.message.to_python()], 'score': score}, f)

        # отправляем ответ пользователю и следующий вопрос
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, response_text)
        if score == 0:
            await bot.send_message(callback_query.from_user.id, f'Игра окончена! Ваш счет: {score}')
            current_question_index = 0
            prevId.clear()
            await bot.send_message(callback_query.from_user.id, f"/quiz-сыграть еще, /exit - посмотреть счет")
        else:
            if current_question_index >= len(questions):
                # Если список вопросов закончился, отправляем сообщение с общим количеством очков игрока
                await bot.send_message(callback_query.from_user.id, f"Игра окончена! Ваш счет: {score}")
                current_question_index = 0
                prevId.clear()
                await bot.send_message(callback_query.from_user.id, f"/quiz-сыграть еще, /exit - посмотреть счет")
                return
            await quiz(callback_query.message)

    # Обработчик ошибок с логированием
    @dp.errors_handler()
    async def errors_handler(update, exception):
        logging.exception(exception)
        return True

    executor.start_polling(dp, skip_updates=True)