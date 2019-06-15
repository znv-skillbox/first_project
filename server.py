from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor


class Post:
    # будем использовать логин как некий Id
    user: str
    # date:
    text: str

    def __init__(self, user: str, text: str):
        self.user = user
        self.text = text

    def __str__(self):
        return f"{self.user}: {self.text}"


class Client(Protocol):
    ip: str = None
    login: str = None
    factory: 'Chat'

    def __init__(self, factory):
        """
        Инициализация фабрики клиента
        :param factory:
        """
        self.factory = factory

    def __eq__(self, other):
        # сравнение объектов по их логину
        return self.login.lower() == other.login.lower()

    def connectionMade(self):
        """
        Обработчик подключения нового клиента
        """
        self.ip = self.transport.getHost().host
        self.factory.clients.append(self)

        print(f"Client connected: {self.ip}")

        self.transport.write("Welcome to the chat v0.1\n".encode())

    def dataReceived(self, data: bytes):
        """
        Обработчик нового сообщения от клиента
        :param data:
        """
        message = data.decode().replace('\n', '')

        if self.login is not None:

            new_post = Post(self.login, message)
            self.factory.posts.append(new_post)

            self.factory.notify_all_users(new_post)

            print(new_post)
        else:
            if message.startswith("login:"):
                self.login = message.replace("login:", "")

                duplicate_user = self.factory.clients.count(self)

                if duplicate_user == 1:
                    notification = f"New user connected: {self.login}"

                    self.factory.notify_all_users(notification)
                    print(notification)

                    # формируем истотрию сообщений для подключившегося пользователя и отправялем ему
                    last_posts = self.get_history(3)
                    history = self.format_hystory(last_posts)

                    self.factory.notify_current_users(self, history)
                else:
                    print(f"Error: Duplicate user = {self.login}")
                    self.factory.clients.remove(self)
                    self.factory.notify_current_users(self, "Access deneid")
            else:
                print("Error: Invalid client login")

    def get_history(self, amount: int = 10):
        """
        получить последние сообщения в истории
        в будущем можно фильтровать сообщения по дате или как-то еще
        :type amount: количество последних сообщений
        """
        return self.factory.posts[amount * (-1):]

    def format_hystory(self, posts: list):
        """
        формируем историю сообщений для отправки
        :type posts: список сообщений
        :return:
        """
        if len(posts) > 0:
            # не знаю почему перед отправкой '\n'.join(posts) стал выдавать ошибку
            # __str__ для Post определил сразу
            # было условие отпраивть до 8 вечера поэтому отправляю так как заработало
            return '\n'.join(str(p) for p in posts) + "\n" + "*" * 20 + "\n"
        else:
            return "No one has written here...\n"

    def connectionLost(self, reason=None):
        """
        Обработчик отключения клиента
        :param reason:
        """
        self.factory.clients.remove(self)
        print(f"Client disconnected: {self.ip}")


class Chat(Factory):
    clients: list
    posts: list

    def __init__(self):
        """
        Инициализация сервера
        """
        self.clients = []
        self.posts = []
        print("*" * 10, "\nStart server \nCompleted [OK]")

    def startFactory(self):
        """
        Запуск процесса ожидания новых клиентов
        :return:
        """
        print("\n\nStart listening for the clients...")

    def buildProtocol(self, addr):
        """
        Инициализация нового клиента
        :param addr:
        :return:
        """
        return Client(self)

    def notify_all_users(self, data: str):
        """
        Отправка сообщений всем текущим пользователям
        :param data:
        :return:
        """
        for user in self.clients:
            self.notify_current_users(user, data)

    @staticmethod
    def notify_current_users(user: Client, data: str):
        """
        Отправка сообщений пользователю
        :param user:
        :param data:
        :return:
        """
        user.transport.write(f"{data}\n".encode())


if __name__ == '__main__':
    reactor.listenTCP(7410, Chat())
    reactor.run()
