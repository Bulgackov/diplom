from handler.helper.message_sender import MessageSender


class BaseHandler(MessageSender):

    def keywords(self):
        return []

    def normalized_keywords(self):
        return [keyword.lower() for keyword in self.keywords()]

    def should_handle(self, message):
        return message.lower() in self.normalized_keywords()

    def is_active(self):
        return False

    def handle(self, message):
        if not self.should_handle(message) and not self.is_active():
            return False
        self.handle_impl(message)
        return True

    def handle_impl(self, message):
        pass
    
from handler.base_handler import BaseHandler


class FallbackHandler(BaseHandler):

    def should_handle(self, _message):
        return True

    def handle_impl(self, _message):
        self.write_msg('Не понимаю о чем вы...')
        
from handler.base_handler import BaseHandler


class FarewellHandler(BaseHandler):

    def keywords(self):
        return ['Пока', 'Bye']

    def handle_impl(self, _message):
        self.write_msg(f'Грустно видеть, как ты уходишь :(\nПока!')
        
from handler.base_handler import BaseHandler


class GreetingsHandler(BaseHandler):

    def keywords(self):
        return ['Привет', 'Hello', 'VKinder', 'ВКиндер']

    def handle_impl(self, _message):
        self.write_msg(f'Добро пожаловать в VKinder!\n ' \
                   f'Сервис предназначенный для романтических знакомств в соответствии с заданными параметрами ' \
                   f'(возраст, пол, город, семейное положение) и с учётом геолокации.\n' \
                   f'Напишите "Старт" для начала работы')
        
from random import randrange
from handler.base_handler import BaseHandler
from handler.question.age_from_question import AgeFromQuestion
from handler.question.age_to_question import AgeToQuestion
from handler.question.hometown_question import HometownQuestion
from handler.question.sex_question import SexQuestion
from handler.question.status_question import StatusQuestion
from handler.question.token_question import TokenQuestion
from model.user import User
from model.candidate import Candidate
from model.photo import Photo
from vk_api import VkApi


class SearchHandler(BaseHandler):

    def __init__(self, user_id, vk_group_client, db_session):
        self.questions = []
        self.search_params = {}
        self.vk_user_client = None
        self.db_session = db_session
        super().__init__(user_id, vk_group_client)

    def reset(self):
        self.search_params = {}
        self.questions = [
            AgeFromQuestion(self.user_id, self.vk_group_client),
            AgeToQuestion(self.user_id, self.vk_group_client),
            HometownQuestion(self.user_id, self.vk_group_client),
            SexQuestion(self.user_id, self.vk_group_client),
            StatusQuestion(self.user_id, self.vk_group_client),
            TokenQuestion(self.user_id, self.vk_group_client, self.db_session),
        ]

    def keywords(self):
        return ['Старт', 'Start']

    def is_active(self):
        for question in self.questions:
            if question.should_handle_answer():
                return True
        return False

    def handle_impl(self, message):
        if self.should_handle(message):
            self.reset()

        question = self.questions[0]
        if question.should_handle_answer():
            if not question.handle_answer(message, self.search_params):
                question.ask()
            else:
                self.questions.pop(0)

        while len(self.questions) > 0 and not self.is_active():
            question = self.questions[0]
            if question.should_ask():
                question.ask()
            else:
                self.questions.pop(0)

        if len(self.questions) == 0:
            self.find_match()

    def find_match(self):
        user = self.db_session.query(User).filter(User.id == self.user_id).first()
        self.vk_user_client = VkApi(token=user.token)
        candidates = self.search()

        if len(candidates) == 0:
            self.write_msg('Никого не найдено')
            return

        for candidate in candidates:
            top_photos = self.get_popular_profile_photos(candidate['id'])
            candidate['top_photos'] = top_photos
            result = f"{candidate['first_name']} {candidate['last_name']}\n"
            result += f"https://vk.com/{candidate['screen_name']}\n"

            candidate_exists = self.db_session.query(Candidate).filter(Candidate.id == candidate['id']).first()
            if not candidate_exists:
                c = Candidate(
                    id=candidate['id'],
                    first_name=candidate['first_name'],
                    last_name=candidate['last_name'],
                    screen_name=candidate['screen_name'],
                )
                self.db_session.add(c)
                user.candidates.append(c)
            else:
                user.candidates.append(candidate_exists)

            self.write_msg(result)

            attachments = []
            for photo in top_photos:
                owner_photo_id = f"photo{photo['owner_id']}_{photo['id']}"
                attachments.append(owner_photo_id)
                photo_exists = self.db_session.query(Photo).filter(Photo.id == owner_photo_id).first()
                if not photo_exists:
                    self.db_session.add(
                        Photo(
                            id=owner_photo_id,
                            photo_id=photo['id'],
                            candidate_id=photo['owner_id'],
                            likes_count=photo['likes']['count'],
                            comments_count=photo['comments']['count'],
                        )
                    )
            self.send_attachment(','.join(attachments))
        self.db_session.commit()

    def send_attachment(self, attachment):
        self.vk_group_client.method('messages.send', {'user_id': self.user_id, 'attachment': attachment,
                                                      'random_id': randrange(10 ** 7)})

    def get_popular_profile_photos(self, owner_id):
        response = self.vk_user_client.method('photos.get', {'owner_id': owner_id, 'album_id': 'profile', 'extended': 1,
                                                             'count': 1000})
        items = response['items']

        def sum_likes_and_comments_count(item):
            return item['likes']['count'] + item['comments']['count']

        items.sort(key=sum_likes_and_comments_count)

        most_liked_photos = items[-3:]
        return most_liked_photos

    def search(self):
        params = {'has_photo': 1, 'count': 10, 'fields': 'screen_name'}
        response = self.vk_user_client.method('users.search', {**self.search_params, **params})

        def already_matched(user_id, candidate_id):
            user = self.db_session.query(User).filter(User.id == user_id, User.candidates.any(id=candidate_id)).first()
            return user is not None

        items = [item for item in response['items'] if
                 not item['is_closed'] and not already_matched(self.user_id, item['id'])]
        return items
