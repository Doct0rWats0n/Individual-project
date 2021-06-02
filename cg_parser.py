import bs4
import requests
import re
import pymorphy2

# Заголовки, чтобы вк определял программу как обычного пользователя и выдавал страницы как для пользователя
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)' +
                  ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
}

# Список с ключевыми словами, по которым будет определяться, что текст
# является уведомлением о соревновании
key_words = [
    'чемпионат', 'участие', 'приглашать', 'олимпиада', 'время',
    'место', 'зарегистрироваться', 'соревнование', 'спартакиада', 'хакатон',
    'конкурс', 'участник'
]


def analyse_text(text):
    """
    Раскладывает переданный текст на слова и ищет среди них ключевые,
    после чего добавляет их в словарь
    :param text: Текст для анализа
    :return:
    """
    morph = pymorphy2.MorphAnalyzer()
    data = {}
    letter = 'йцукенгшщзхъфывапролджэячсмитьбюqwertyuiopasdfghjklzxcvbnm '
    text = text.lower()
    for symbol in text:
        if symbol not in letter:
            text = text.replace(symbol, ' ')
    words = text.split()
    for word in words:
        morphed = morph.parse(word)[0]
        if morphed and morphed.normal_form in key_words:
            data[morphed.normal_form] = data.get(morphed.normal_form, 0) + 1
    return data


def parse_page(link, db, id_to_stop=None):
    """
    Парсит группы, после чего анализирует текст записей группы. В случае, если
    в тексте найдено большое количество ключевых слов, возвращает id этой записи
    :param link: Ссылка на группу в ВКонтакте
    :param db: База данных для обновления ссылок и/или добавления новых значений
    :param id_to_stop: id последней отправленной записи
    :return: Возвращает id записей в группе
    """
    soup = bs4.BeautifulSoup(requests.get(link, headers=headers).text, 'html.parser')
    # Ищет раздел с постами в группе
    if len(soup.find_all('div', {'class': re.compile('wall_posts')})[0].find_all(
            'div', {'id': re.compile('post-'), 'class': re.compile('_post post')})) == 1:
        wall = soup.find_all('div', {'class': re.compile('wall_posts')})[1]
    else:
        wall = soup.find_all('div', {'class': re.compile('wall_posts')})[0]

    # Ищет id постов
    posts_id = [
        f'post-{link.get("href").split("-")[1]}' for link in wall.find_all('a', {
            'class': 'post_link'
        })
    ]
    values = []
    # Если последнего id нет, смотрит 10 последних записей и добавляет id в базу
    if id_to_stop is None:
        for value in posts_id:
            post = wall.find('div', {'id': value})
            post_text = post.find('div', {'class': 'wall_post_text'})
            if post_text:
                words = analyse_text(post_text.text.strip())
                if sum(words.values()) > 13:
                    values.append((value, value[value.find('-'):]))
        db.update_value(link, posts_id[0])
    # Если последний id есть, смотрит, не является ли он первым в списке полученных id.
    # Если является, это значит, что в группе не появилось новых записей и парсить нечего.
    elif id_to_stop != posts_id[0]:
        for value in posts_id:
            if id_to_stop == value:
                break
            post = wall.find('div', {'id': value})
            post_text = post.find('div', {'class': 'wall_post_text'})
            if post_text:
                words = analyse_text(post_text.text.strip())
                if sum(words.values()) > 13:
                    values.append((value, value[value.find('-'):]))
        db.update_value(link, posts_id[0])
    else:
        pass
    return values


def main(db):
    """
    Проверяет все группы в переданной базе данных
    на наличие новых постов, и возвращает их id
    :param db:
    """
    data = db.select_all()
    id_s = []
    for group, post in data:
        id_s += parse_page(group, db, post)
    return id_s
