from random import randrange


class MessageSender:

    def __init__(self, user_id, vk_group_client):
        self.vk_group_client = vk_group_client
        self.user_id = user_id

    def write_msg(self, message):
        self.vk_group_client.method('messages.send', {'user_id': self.user_id, 'message': message, 'random_id': randrange(10 ** 7)})
        
from handler.question.base_question import BaseQuestion


class AgeFromQuestion(BaseQuestion):
    def question(self):
        return 'Укажите минимальный возраст: '

    def is_valid_answer(self, answer, params):
        try:
            answer = int(answer)
            return 13 <= answer <= 100
        except ValueError:
            return False

    def get_param_name(self):
        return 'age_from'
      
from handler.question.base_question import BaseQuestion


class AgeToQuestion(BaseQuestion):
    def question(self):
        return 'Укажите максимальный возраст: '

    def is_valid_answer(self, answer, params):
        try:
            answer = int(answer)
            return 13 <= answer <= 100 and int(params['age_from']) <= answer
        except ValueError:
            return False

    def get_param_name(self):
        return 'age_to'
      
 from handler.helper.message_sender import MessageSender
import enum


class QuestionState(enum.Enum):
    NOT_ASKED = 0
    ASKED = 1
    FULFILLED = 2


class BaseQuestion(MessageSender):

    def __init__(self, user_id, vk_group_client):
        self.state = QuestionState.NOT_ASKED
        super().__init__(user_id, vk_group_client)

    def question(self):
        return ''

    def is_valid_answer(self, _answer, _params):
        return True

    def get_param_name(self):
        return ''

    def should_ask(self):
        return self.state == QuestionState.NOT_ASKED

    def ask(self):
        self.state = QuestionState.ASKED
        self.write_msg(self.question())

    def should_handle_answer(self):
        return self.state == QuestionState.ASKED

    def handle_answer(self, answer, params):
        is_valid = self.is_valid_answer(answer, params)
        if is_valid:
            self.state = QuestionState.FULFILLED
            params[self.get_param_name()] = answer
        return is_valid
      
from handler.question.base_question import BaseQuestion


class HometownQuestion(BaseQuestion):
    def question(self):
        return 'Город рождения: '

    def is_valid_answer(self, answer, params):
        return True

    def get_param_name(self):
        return 'hometown'
      
from handler.question.base_question import BaseQuestion


class SexQuestion(BaseQuestion):
    def question(self):
        return 'Введите пол человека(1-м, 2-ж, 0-любой)'

    def is_valid_answer(self, answer, params):
        try:
            answer = int(answer)
            return answer in [1, 2, 0]
        except ValueError:
            return False

    def get_param_name(self):
        return 'sex'
      
from handler.question.base_question import BaseQuestion


class StatusQuestion(BaseQuestion):
    def question(self):
        return 'Выберите семейное положение (1-не женат(незамужем),' \
               '2-всречается, 3-помолвлен(а), 4-женат(замужем), 5-все сложно,' \
               ' 6-в поисках, 7-в любви): '

    def is_valid_answer(self, answer, params):
        try:
            answer = int(answer)
            return 1 <= answer <= 7
        except ValueError:
            return False

    def get_param_name(self):
        return 'status'
      
from handler.question.base_question import BaseQuestion, QuestionState
from model.user import User
import re

CLIENT_ID = '<CLIENT-ID>'
AUTH_LINK = 'https://oauth.vk.com/authorize?client_id=' + CLIENT_ID + '&display=page&scope=status.offline&response_type=token&v=5.92'


class TokenQuestion(BaseQuestion):
    def __init__(self, user_id, vk_group_client, db_session):
        self.db_session = db_session
        super().__init__(user_id, vk_group_client)

    def question(self):
        return 'Напишите ваш токен. Токен можно получить по этой ссылке: ' + AUTH_LINK

    def is_valid_answer(self, answer, params):
        return re.match('^[a-zA-Z0-9]+$', answer) is not None

    def should_ask(self):
        user = self.db_session.query(User).filter(User.id == self.user_id).first()
        return super().should_ask() and not user.token

    def handle_answer(self, answer, params):
        is_valid = self.is_valid_answer(answer, params)
        if is_valid:
            self.state = QuestionState.FULFILLED
            user = self.get_user()
            user.token = answer
            self.db_session.commit()
        return is_valid

    def get_user(self):
        return self.db_session.query(User).filter(User.id == self.user_id).first()
