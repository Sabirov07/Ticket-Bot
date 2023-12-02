import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from notification_manager import NotificationManager
from data_manager import DataManager
from flight_search import FlightSearch
from flight_data import FlightData
import logging


async def start(update: Update, context: CallbackContext) -> None:
    """Send initial message and prompt user to enter the city."""
    user_name = update.message.from_user.first_name
    user_id = update.message.from_user.id

    welcome_message = (
        f"Hi {user_name}! 👋 Welcome to SS bot. Here is what I can do:\n"
        f"– Search for cheapest flights 🔎\n"
        f"– Track tickets prices 👀\n"
        f"– Notify about price changes 🔔\n\n"
        f"Shall we start? 👇"
    )

    await update.message.reply_text(welcome_message)

    registration_data[user_id] = {'state': 'city'}
    await update.message.reply_text("Which city are you interested in🤩? (e.g., Tashkent): ")


async def search(update: Update, context: CallbackContext):
    """Initiate the flight search."""
    chat_id = update.message.chat_id

    if sheet_data is None:
        await update.message.reply_text('Development in progress🏗\nPlease try again later⌛️.')
        return

    await update.message.reply_text("Here are some tickets from Warsaw🔍...")
    cities = [city_data['city'] for city_data in sheet_data]
    numbered_cities = [f"{index + 1}. {city}" for index, city in enumerate(cities)]

    midpoint = len(numbered_cities) // 2

    columns = list(zip(numbered_cities[:midpoint], numbered_cities[midpoint:]))

    message_text = "\n".join([f"{col[0]:<40}{col[1]:<40}" for col in columns])
    await update.message.reply_text(message_text, parse_mode='Markdown')

    await search_and_handle_flight(update, context, 0, chat_id)


async def search_and_handle_flight(update: Update, context: CallbackContext, city_index: int, chat_id=None):
    """Search for flights for a city and handle the results."""
    query = update.callback_query
    city = sheet_data[city_index]

    # Perform the flight search
    search_data = flight_search.search_flight(city['iataCode'])

    if not search_data:
        message = f"Sorry, no available flights for {city['city']}. Try other cities!"
        await context.bot.send_message(chat_id=chat_id, text=message)
        city = sheet_data[1]
        search_data = flight_search.search_flight(city['iataCode'])

    message_text, reply_markup = await generate_flight_message_and_markup(city_index, search_data, city['iataCode'])
    if query:
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='HTML',
                                      disable_web_page_preview=True)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='HTML',
                                        disable_web_page_preview=True)
    return city, search_data


async def generate_flight_message_and_markup(city_index, search_data, city_code):
    """Generate the message and markup for flight information."""
    flights_text = [
        f"{i + 1}) {city_code} ({search_data.out_date}) - €{search_data.price}\n Stops🔄: {search_data.stops}"
        f"\nBuy ticket <a href='{search_data.deeplink}'>Click Here</a>"
        for i, search_data in enumerate(search_data)
    ]
    message_text = f"{int(city_index) + 1}. 📍 Warsaw Chopin - {search_data[0].destination_city}\n\n" + \
                   "\n______________________________\n\n".join(flights_text)
    keyboard = [
        [
            InlineKeyboardButton("<", callback_data="previous"),
            InlineKeyboardButton("Track Ticket", callback_data=str(city_index)),
            InlineKeyboardButton(">", callback_data="next"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return message_text, reply_markup


async def callback_handler(update: Update, context: CallbackContext) -> None:
    """Handle callback queries - Track the chosen city."""
    query = update.callback_query
    chat_id = query.message.chat_id
    callback_data = query.data
    user_data = context.user_data
    city_index = context.user_data.setdefault('city_index', 0)

    if callback_data in {"next", "previous"}:
        if callback_data == "next":
            city_index = (city_index + 1) % len(sheet_data)
        elif callback_data == "previous":
            city_index = (city_index - 1) % len(sheet_data)

        user_data['city_index'] = city_index
        await search_and_handle_flight(update, context, city_index, chat_id)
        return

    chosen_city, search_data = await search_and_handle_flight(update, context, int(callback_data))
    tracked_tickets[chat_id] = {'city': chosen_city['city'], 'city_code': chosen_city['iataCode'],
                                'initial_price': search_data[0].price}

    print("TRACKING DATA SAVED AS:")
    print(tracked_tickets)

    await query.message.reply_text(
        text=f"The price for <a href='{search_data[0].deeplink}'>{chosen_city['city']}</a> is being tracked👀"
             f"\nWe'll notify you of any price changes📩",
        parse_mode='HTML', disable_web_page_preview=True)
    return


async def check_price_changes(context: CallbackContext):
    print('check_price_changes...')
    try:
        for chat_id, ticket_info in tracked_tickets.items():
            city = ticket_info['city']
            city_code = ticket_info['city_code']
            initial_price = ticket_info['initial_price']
            print(ticket_info['initial_price'])

            search_data = flight_search.search_flight(city_code)
            current_price = search_data[0].price
            link = search_data[0].deeplink

            if current_price != initial_price:
                print("PRICE CHANGE")
                tracked_tickets[chat_id]['initial_price'] = current_price
                price_change = current_price - initial_price
                price_direction = 'increased' if price_change > 0 else 'decreased'
                message = (
                    f"🚨 Price Alert! 🚨\n\n"
                    f"The price for {city} ticket has {price_direction} to €{current_price}.\n"
                    f"🔗 [Click Here to View and Buy the Ticket]({link})."
                )
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown',
                                               disable_web_page_preview=True)

    except Exception as e:
        logging.exception("An error occurred in check_price_changes: %s", str(e))


async def handle_register(update: Update, context: CallbackContext):
    """Handle user information during registration."""
    user_name = update.message.from_user.first_name
    user_id = update.message.from_user.id
    text = update.message.text

    try:
        state = registration_data[user_id].get('state')
    except KeyError:
        await update.message.reply_text("Sorry, you cannot type directly. Please choose one of the above👆🏿")
        return

    if state == 'city':
        is_valid_city = validate_city(text)
        if is_valid_city:
            registration_data[user_id]['interested_city'] = text
            await update.message.reply_text("Enter your Email: ")
            registration_data[user_id]['state'] = 'email'
        else:
            await update.message.reply_text(
                "Sorry, the entered city is not valid. Please enter a valid city.")
    elif state == 'email':
        registration_data[user_id]['email'] = text
        await update.message.reply_text("Enter your Email again: ")
        registration_data[user_id]['state'] = 'email_retype'
    elif state == 'email_retype':
        if text == registration_data[user_id]['email']:
            data_manager.register(user_name, user_id, registration_data[user_id]['interested_city'],
                                  registration_data[user_id]['email'])
            await update.message.reply_text(
                f"Thanks for subscribing {user_name}!\nTry /search 👈🏿")
            del registration_data[user_id]
        else:
            await update.message.reply_text("Emails do not match. Please try again.")
            registration_data[user_id]['state'] = 'email'


def validate_city(city):
    """Validate the entered city."""
    capitalized_city = city.capitalize()
    valid_cities = FlightData.get_valid_cities()
    if capitalized_city in valid_cities:
        index_to_move = next(
            (index for index, city_data in enumerate(sheet_data) if city_data['city'][:2] == capitalized_city),
            None)
        code = flight_search.get_iata(capitalized_city)
        if index_to_move is not None:
            sheet_data.pop(index_to_move)
            print(f'Did not added: {capitalized_city} already exists')
        else:
            print('New city=======', capitalized_city)
            data_manager.add_new_city(capitalized_city, code)

        sheet_data.insert(0, {'city': capitalized_city, 'iataCode': code})
        return capitalized_city
    else:
        print('Not valid city')
        return None


async def unknown(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command!"
                                                                          "\nTry /Start, /Search")


def main():
    """Start the bot and set up handlers."""
    try:
        logging.info("Starting bot...")

        app = Application.builder().token(TOKEN).build()

        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('search', search))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_register))
        app.add_handler(CallbackQueryHandler(callback_handler))
        app.add_handler(MessageHandler(filters.COMMAND, unknown))

        job_queue = app.job_queue
        job_queue.run_repeating(check_price_changes, interval=10800)
        logging.debug("Queued a task...")

        # Start polling
        app.run_polling()
        logging.debug('Polling...')

    except Exception as e:
        logging.exception("An error occurred: %s", str(e))


if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    # Initialize Classes
    flight_search = FlightSearch()
    data_manager = DataManager()
    notification_manager = NotificationManager()
    sheet_data = data_manager.get_data()

    # Dictionary to hold user data
    registration_data = {}
    tracked_tickets = {}

    main()
