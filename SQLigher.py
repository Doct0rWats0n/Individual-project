import sqlite3


class SQLighter:
    """
    Создает объект, подключенный к базе данных, для
    дальнейшего взаимодействия
    """
    def __init__(self, database, table_name):
        self.connection = sqlite3.connect(database)
        self.cur = self.connection.cursor()
        self.table = table_name

    def select_all(self):
        """ Получаем все строки """
        return self.cur.execute("SELECT * FROM %s" % self.table).fetchall()

    def update_value(self, group_link, post):
        """ Меняет последнюю ссылку на новую последнюю ссылку """
        if self.find_group(group_link):
            self.cur.execute("UPDATE %s SET %s = %s WHERE %s = %s"
                             % (self.table, "last_id", "'" + post + "'", "group_link", "'" + group_link + "'"))
        else:
            self.insert_value((group_link, post))
        self.connection.commit()

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()

    def insert_value(self, value):
        """ Добавляет запись в таблицу """
        if len(value) == 1:
            self.cur.execute("INSERT INTO %s VALUES ('%s')" % (self.table, value[0]))
        else:
            self.cur.execute("INSERT INTO {} VALUES {}".format(self.table, value))
        self.connection.commit()

    def find_group(self, group_link):
        """ Ищет значение в таблице"""
        values = self.cur.execute("SELECT * FROM %s WHERE %s = %s" %
                                  (self.table, "group_link", "'" + group_link + "'")).fetchone()
        return values

    def delete_value(self, value, column):
        self.cur.execute("DELETE FROM %s WHERE %s = %s" % (self.table, column, "'" + value + "'"))
        self.connection.commit()
