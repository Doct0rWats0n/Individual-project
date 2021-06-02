import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import config
from SQLigher import SQLighter
from cg_parser import main
from time import sleep
from threading import Thread

# Подключение к боту в ВКонтакте
vk_ses = vk_api.VkApi(token=config.TOKEN)
# Создание переменной для "прослушивания" событий на сервере
longpoll = VkLongPoll(vk_ses)
# База данных с пользователями и группами в ВКонтакте
user_base = SQLighter('users.db', 'users')
group_base = SQLighter('groups.db', 'groups')


def mailing():
    """
    Проверяет группы на наличие новых записей о соревнованиях и, в случае
    их обнаружения, рассылает всем пользователям, подписавшимся на бота
    """
    users, groups = SQLighter('users.db', 'users'), SQLighter('groups.db', 'groups')
    while True:
        print('Начало рассылки')
        ids = main(groups)
        print(ids)
        people = users.select_all()
        if ids:
            for post in ids:
                attachment = 'wall%s_%s' % (post[1], post[0])
                for man in people:
                    vk_ses.method('messages.send', {
                        'user_id': man[0],
                        'attachment': attachment,
                        'random_id': 0
                    })
                    # ses_api.messages.send(user_id=man, message=link, random_id=0)
        print('Конец рассылки')
        sleep(60 * 5)


# Создание отдельного потока для функции проверки групп на
# новые записи о соревнованиях
mail_bot = Thread(target=mailing)
mail_bot.start()

# Смотрит все события, произошедшие на сервере
#
# Если пользователь отправил сообщение "Подписаться", добавляет
# его в пользовательскую базу данных
#
# Если же пользователь отправил сообщение "Отписаться", удаляет
# его из базы данных
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            msg = event.text.lower()
            user_id = event.user_id
            values = [value[0] for value in user_base.select_all()]
            print(values)

            if msg == 'подписаться':
                if str(user_id) in values:
                    vk_ses.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Вы уже подписаны на рассылку',
                        'random_id': 0
                    })
                else:
                    user_base.insert_value((str(user_id),))
                    vk_ses.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Вы подписались на рассылку',
                        'random_id': 0
                    })
            elif msg == 'отписаться':
                if str(user_id) in values:
                    user_base.delete_value(str(user_id), 'user_id')
                    vk_ses.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Вы отписались от рассылки',
                        'random_id': 0
                    })
