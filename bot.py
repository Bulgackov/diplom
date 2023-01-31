from handler.fallback_handler import FallbackHandler
from handler.farewell_handler import FarewellHandler
from handler.greetings_handler import GreetingsHandler
from handler.search_handler import SearchHandler
from model.user import User


class VkBot:

    def __init__(self, user_id, vk_group_client, db_session):
        self.user_id = user_id
        self.db_session = db_session
        self.handlers = [
            GreetingsHandler(user_id, vk_group_client),
            FarewellHandler(user_id, vk_group_client),
            SearchHandler(user_id, vk_group_client, db_session),
            FallbackHandler(user_id, vk_group_client),
        ]
        self.last_handler = None
        self.create_user_if_not_exists()

    def create_user_if_not_exists(self):
        exists = self.db_session.query(User).filter(User.id == self.user_id).first()
        if not exists:
            self.db_session.add(User(id=self.user_id))
            self.db_session.commit()

    def handle_new_message(self, message):
        if self.last_handler is not None and self.last_handler.is_active():
            self.last_handler.handle(message)
            return

        for handler in self.handlers:
            if handler.handle(message):
                self.last_handler = handler
                break
