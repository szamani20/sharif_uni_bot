import time
import telepot
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, PickleType, String
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://username:password@localhost:5432/database_name')
Base = declarative_base()


class Chat:
    def __init__(self, id, first_name, username=None, last_name=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def dump(self):
        return 'id:' + str(self.id) + \
               ' username:' + str(self.username) + \
               ' first_name:' + str(self.first_name) + \
               ' last_name:' + str(self.last_name)


class TextMessage:
    def __init__(self, text, message_id, chat):
        self.text = text
        self.message_id = message_id
        self.chat = chat

    def dump(self):
        return 'text:' + str(self.text) + \
               ' message_id:' + str(self.message_id) + \
               ' chat:' + self.chat.dump()


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    event_name = Column(String(100), nullable=False)
    event_date = Column(String(100), nullable=False)
    event_hour = Column(String(100), nullable=True)
    event_location = Column(String(100), nullable=True)
    event_description = Column(String(1000), nullable=True)
    event_chat = Column(PickleType(), nullable=False)

    def __init__(self, event_name=None, event_date=None, event_hour=None, event_location=None, event_description=None,
                 event_chat=None):
        self.event_name = event_name
        self.event_date = event_date
        self.event_hour = event_hour
        self.event_location = event_location
        self.event_description = event_description
        self.event_chat = event_chat

    def inform(self):
        return self.event_name + \
               '\n' + self.event_date + \
               '\n' + self.event_hour + \
               '\n' + self.event_location + \
               '\n' + self.event_description

    def dump(self):
        return 'event_name:' + self.event_name + \
               '\nevent_date:' + self.event_date + \
               '\nevent_hour:' + self.event_hour + \
               '\nevent_location:' + self.event_location + \
               '\nevent_description:' + self.event_description + \
               '\nevent_chat:' + self.event_chat.dump()


events = []
current_event = None


class YourBot(telepot.Bot):
    def __init__(self, *args, **kwargs):
        super(YourBot, self).__init__(*args, **kwargs)
        self._answerer = telepot.helper.Answerer(self)

    def handle(self, msg):
        flavor = telepot.flavor(msg)
        global bot
        global current_event

        print(msg)

        # chat message
        if flavor == 'chat':
            content_type, chat_type, chat_id = telepot.glance(msg)
            print(content_type, chat_type, chat_id)

            if content_type == 'text':
                chat = Chat(**msg['from'])
                text_message = TextMessage(msg['text'], msg['message_id'], chat)

                if text_message.text == '/get_last_event':
                    events = session.query(Event).all()
                    if len(events) != 0:
                        bot.sendMessage(chat.id, events[len(events) - 1].inform())

                if text_message.text == '/add_event':
                    current_event = Event()
                    current_event.event_chat = chat  # we should figure out which user is which!
                    bot.sendMessage(chat.id, '1. Tell me the name of the event in reply to this message')

                if 'reply_to_message' in msg:
                    main_chat = Chat(**msg['reply_to_message']['from'])
                    main_message = TextMessage(msg['reply_to_message']['text'], msg['reply_to_message']['message_id'],
                                               main_chat)

                    if '1.' in main_message.text:
                        current_event.event_name = text_message.text
                        bot.sendMessage(chat.id, '2. Tell me the date of the event in reply to this message')

                    if '2.' in main_message.text:
                        current_event.event_date = text_message.text
                        bot.sendMessage(chat.id, '3. Tell me the hour of the event in reply to this message')

                    if '3.' in main_message.text:
                        current_event.event_hour = text_message.text
                        bot.sendMessage(chat.id, '4. Tell me the location of the event in reply to this message')

                    if '4.' in main_message.text:
                        current_event.event_location = text_message.text
                        bot.sendMessage(chat.id,
                                        '5. Tell me the description (any links maybe)'
                                        ' of the event in reply to this message')

                    if '5.' in main_message.text:
                        current_event.event_description = text_message.text
                        session.add(current_event)
                        current_event = None
                        session.commit()
                        bot.sendMessage(chat.id, 'Congratulations, your event has been create. You can see the '
                                                 'list of events using "/get_last_event" command')


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    global session
    Session = sessionmaker(bind=engine)
    session = Session()

    TOKEN = 'contact with @botfather'

    bot = YourBot(TOKEN)
    bot.message_loop()
    print('Listening ...')

    # Keep the program running.
    while 1:
        time.sleep(10)

    print("Bye")
    engine.dispose()
