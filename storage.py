import sqlite3
from datetime import datetime, timedelta
from os.path import dirname, join
from secrets import token_hex


class CursorManager:
    """Class to manage acquiring a cursor and committing afterward."""

    @staticmethod
    def _connection():
        return sqlite3.connect(join(dirname(__file__), 'chatbot.sqlite3'))

    def __enter__(self):
        """Obtain a connection and cursor."""
        self._conn = self._connection()
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit the connection."""
        self._conn.commit()
        return False


class Storage:
    TABLE_NAME = None
    TABLE_SCHEMA = ''

    @property
    def cursor(self):
        return CursorManager()

    def __init__(self):
        if self.TABLE_NAME is None:
            raise NotImplementedError('`TABLE_NAME` needs to be specified.')
        with self.cursor as cursor:
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS {} ({})'.format(self.TABLE_NAME,
                                                            self.TABLE_SCHEMA))

    def __len__(self):
        with self.cursor as cursor:
            return cursor.execute(
                'SELECT Count(*) FROM {}'.format(self.TABLE_NAME)).fetchone()[0]

    def _contains(self, column_name, item):
        with self.cursor as cursor:
            return cursor.execute(
                'SELECT {col} FROM {tab} WHERE {col}=?'.format(tab=self.TABLE_NAME,
                                                               col=column_name),
                (item,)).fetchone()

    def _get_row(self, key_name, value, *columns):
        with self.cursor as cursor:
            return cursor.execute('SELECT {cols} FROM {tab} WHERE {key}=?'.format(
                tab=self.TABLE_NAME, key=key_name, cols=', '.join(columns)),
                (value,)).fetchone()

    def _iterate_column(self, column_name):
        with self.cursor as cursor:
            return (row[0] for row in cursor.execute(
                'SELECT {col} from {tab} ORDER BY {col} ASC'.format(
                    col=column_name,
                    tab=self.TABLE_NAME)))

    def _iterate_columns(self, *columns, order_by=''):
        with self.cursor as cursor:
            return cursor.execute(
                'SELECT {cols} from {tab} {order}'.format(cols=', '.join(columns),
                                                          tab=self.TABLE_NAME,
                                                          order=order_by))

    def _remove(self, column_name, value):
        with self.cursor as cursor:
            cursor.execute(
                'DELETE FROM {tab} WHERE {col}=?'.format(tab=self.TABLE_NAME,
                                                         col=column_name),
                (value,))

    def clear(self):
        with self.cursor as cursor:
            cursor.execute('DROP TABLE {}'.format(self.TABLE_NAME))
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS {} ({})'.format(self.TABLE_NAME,
                                                            self.TABLE_SCHEMA))


class ChatLog(Storage):
    """Class to represent logged chats."""
    TABLE_NAME = 'chatlog'
    TABLE_SCHEMA = ('session_id TEXT NOT NULL, '
                    'message_contents TEXT NOT NULL, '
                    'user_message INTEGER NOT NULL, '
                    'message_time DATETIME NOT NULL')

    def __iter__(self):
        """Iterate over all known chat logs, returning their session IDs."""
        return iter(set(self._iterate_column('session_id')))

    def get(self, session):
        """Get the log of a session.

        :param session: The session identifier.
        :returns: An iterable of (message_contents, is_from_user, timestamp).
        """
        with self.cursor as cursor:
            for text, is_from_user, timestamp in cursor.execute(
                    'SELECT message_contents, user_message, message_time FROM {tab} WHERE session_id=? '
                    'ORDER BY message_time ASC'.format(
                        tab=self.TABLE_NAME),
                    (session,)):
                yield text, bool(is_from_user), datetime.fromtimestamp(timestamp)

    def log(self, session, message, is_from_user):
        """Add a log entry.

        :param session: The session ID.
        :param message: The message contents as str.
        :param is_from_user: Whether or not the message is from the user, as a bool.
        """
        with self.cursor as cursor:
            cursor.execute('INSERT INTO {} VALUES (?, ?, ?, ?)'.format(
                self.TABLE_NAME),
                (session, message, is_from_user, int(datetime.now().timestamp())))


class Cookies(Storage):
    TABLE_NAME = 'cookies'
    TABLE_SCHEMA = 'id INTEGER PRIMARY KEY NOT NULL, cookie TEXT NOT NULL, expiration DATETIME NOT NULL'
    VALID_LENGTH = timedelta(days=7)

    def check(self, cookie):
        """Check if a cookie is valid."""
        with self.cursor as cursor:
            return cursor.execute('SELECT * FROM {} WHERE cookie=? AND expiration>?'.format(self.TABLE_NAME),
                                  (cookie, int(datetime.now().timestamp()))).fetchone() is not None

    def new(self):
        """Store a new cookie and return it."""
        val = token_hex(30)
        exp_date = int((datetime.now() + self.VALID_LENGTH).timestamp())
        with self.cursor as cursor:
            cursor.execute('INSERT INTO {} VALUES (NULL, ?, ?)'.format(self.TABLE_NAME), (val, exp_date))
        return val

    def prune(self):
        """Remove cookies that are out-of-date."""
        now = int(datetime.now().timestamp())
        with self.cursor as cursor:
            cursor.execute('DELETE FROM {} WHERE expiration < ?'.format(self.TABLE_NAME), (now,))

    def remove(self, cookie):
        """Remove a cookie as part of a logout."""
        self._remove('cookie', cookie)


class Images(Storage):
    """Class to store image blobs."""
    TABLE_NAME = 'images'
    TABLE_SCHEMA = 'img_name TEXT PRIMARY KEY NOT NULL, image BLOB NOT NULL, mimetype TEXT NOT NULL'

    def __getitem__(self, name):
        """Get an image.

        :param name: The name of the image.
        :returns: A tuple containing (The image, as bytes; the mimetype, as str)
        """
        with self.cursor as cursor:
            result = cursor.execute('SELECT image, mimetype FROM {} WHERE img_name=?'.format(self.TABLE_NAME),
                                    (name,)).fetchone()
        if result is None:
            raise KeyError('No known image called {!r}.'.format(name))
        return result

    def __iter__(self):
        """Iterate over all known images, returning their names."""
        return self._iterate_column('img_name')

    def set(self, name, image, mimetype):
        """Save an image.

        :param name: The name of the image.
        :param image: The image, as bytes.
        :param mimetype: The mimetype of the image.
        """
        with self.cursor as cursor:
            cursor.execute('REPLACE INTO {} VALUES (?, ?, ?)'.format(self.TABLE_NAME), (name, image, mimetype))

    def get(self, name, default=(None, None)):
        """Get an image or return a default value.

        :param name: The name of the image.
        :param default: What to return if the image isn't found (default: (None, None))
        :returns: A tuple containing (The image, as bytes; the mimetype, as str), or the default.
        """
        try:
            return self[name]
        except KeyError:
            return default

    def remove(self, name):
        """Remove an image.

        :param name: The name of the image.
        """
        self._remove('img_name', name)


class Prompts(Storage):
    """Class to store the prompts and defaults of Exchanges."""
    TABLE_NAME = 'prompts'
    TABLE_SCHEMA = ('name TEXT PRIMARY KEY NOT NULL, prompt TEXT NOT NULL, '
                    'def TEXT, rank INTEGER, type TEXT')

    def __iter__(self):
        """Iterate over the names, prompts, defaults, and types of Exchanges."""
        return self._iterate_columns('name', 'prompt', 'def', 'type', order_by='ORDER BY rank ASC')

    def delete(self, name):
        """Delete an Exchange from the Prompts table.

        :param name: The name of the Exchange.
        """
        self._remove('name', name)

    def get(self, name):
        """Get an Exchange's prompt and default successor in one query.

        :param name: The name of the Exchange.
        :returns the prompt and the default, as a tuple.
        """
        return self._get_row('name', name, 'prompt', 'def')

    def get_default(self, name):
        """Get the name of an Exchange's default successor Exchange.

        :param name: The name of the Exchange.
        :returns: The name of the successor as a str, if it exists, otherwise
            None.
        """
        row = self._get_row('name', name, 'def')
        if row:
            row = row[0]
        return row

    def get_prompt(self, name):
        """Get an Exchange's prompt.

        :param name: The name of the Exchange.
        :returns: The prompt for the Exchange, as a str.
        """
        row = self._get_row('name', name, 'prompt')
        if row:
            row = row[0]
        return row

    def get_rank(self, name):
        """Get an Exchange's rank.

        :param name: The name of the Exchange.
        :returns: The rank of the Exchange, as an int.
        """
        return self._get_row('name', name, 'rank')[0]

    def get_type(self, name):
        """Get an Exchange's type.

        :param name: The type of the Exchange.
        :returns: The type of the Exchange, as a str.
        """
        return self._get_row('name', name, 'type')[0]

    def set(self, name, prompt, default=None, rank=None, type_=None):
        """Set the prompt for an Exchange.

        :param name: The name of the Exchange.
        :param prompt: The prompt for the Exchange.
        :param default: The default target Exchange of this Exchange
            (default: None).
        :param rank: The rank of this Exchange (default: None)
        :param type_: The type of this Exchange (default: None)
        """
        with self.cursor as cursor:
            cursor.execute('REPLACE INTO {} VALUES (?, ?, ?, ?, ?)'.format(
                self.TABLE_NAME),
                (name, prompt, default, rank, type_))


class Tangents(Storage):
    """Class to store a list of tangents."""
    TABLE_NAME = 'tangents'
    TABLE_SCHEMA = 'id INTEGER PRIMARY KEY NOT NULL, rank INTEGER NOT NULL, tangent TEXT NOT NULL'

    def __iter__(self):
        """Iterate over all tangents yielding (id, rank, tangent)."""
        return self._iterate_columns('id', 'rank', 'tangent', order_by='ORDER BY rank ASC')

    def delete(self, id_):
        """Delete a tangent.

        :param id_: The id of the tangent.
        """
        self._remove('id', id_)

    def get(self, id_):
        """Get a tangent's id, rank, and tangent.

        :param id_: The id of the tangent.
        :returns The id, rank, and tangent, as a tuple.
        """
        return self._get_row('id', id_, 'id', 'rank', 'tangent')

    def set(self, rank, tangent, id_=None):
        """Set a tangent.

        :param rank: The rank of the tangent.
        :param tangent: The text of the tangent.
        :param id_: The id of a preexisting tangent to modify (default: None).
        """
        with self.cursor as cursor:
            cursor.execute('REPLACE INTO {} VALUES (?, ?, ?)'.format(
                self.TABLE_NAME),
                (id_, rank, tangent))


class TangentTracker(Storage):
    """Class to track which tangents have been seen by which users."""
    TABLE_NAME = 'tangent_tracker'
    TABLE_SCHEMA = 'tangent_id INTEGER NOT NULL, user_id TEXT NOT NULL'

    def clear_user(self, user_id):
        """Mark all tangents as unseen by a user.

        :param user_id: The id of the user in question.
        """
        self._remove('user_id', user_id)

    def get_all_seen(self, user_id):
        """Return the IDs of all tangents the user has seen.

        :param user_id: The ID of the user.
        :returns: The IDs of all tangents the user has seen, as some kind of iterable.
        """
        with self.cursor as cursor:
            return cursor.execute(
                'SELECT tangent_id from {tab} WHERE user_id=?'.format(
                    tab=self.TABLE_NAME),
                (user_id,)).fetchall()

    def set_seen(self, tangent_id, user_id):
        """Set a user as having seen a particular tangent.

        :param tangent_id: The id of the tangent, an integer.
        :param user_id: The user id, a string.
        """
        with self.cursor as cursor:
            cursor.execute('INSERT INTO {} VALUES (?, ?)'.format(
                self.TABLE_NAME),
                (tangent_id, user_id))


class Keywords(Storage):
    """Class to store the various keywords of Exchanges."""
    TABLE_NAME = 'keywords'
    TABLE_SCHEMA = ('id INTEGER PRIMARY KEY NOT NULL, '
                    'exchange TEXT NOT NULL, '
                    'keyword TEXT NOT NULL, '
                    'destination TEXT NOT NULL')

    def delete(self, name):
        """Delete the keywords of an Exchange.

        :param name: The name of the Exchange.
        """
        self._remove('exchange', name)

    def get_mapping(self, name):
        """Get the keyword to Exchange mapping for an Exchange.

        :param name: The name of the Exchange.
        """
        with self.cursor as cursor:
            response = cursor.execute(
                'SELECT keyword, destination from {tab} WHERE exchange=?'.format(
                    tab=self.TABLE_NAME),
                (name,)).fetchall()
        return dict(response)

    def set(self, name, keyword, destination):
        """Set a keyword for an Exchange.

        :param name: The name of the Exchange.
        :param keyword: The keyword.
        :param destination: The destination Exchange if the keyword is matched.
        """
        self.set_many(name, {keyword: destination})

    def set_many(self, name, keyword_map):
        """Set many keywords for an Exchange.

        :param name: The name of the Exchange.
        :param keyword_map: A dict mapping keywords to Exchanges.
        """
        with self.cursor as cursor:
            for keyword, destination in keyword_map.items():
                pre_existing = cursor.execute(
                    'SELECT destination from {tab} WHERE '
                    'exchange=? AND keyword=?'.format(
                        tab=self.TABLE_NAME), (name, keyword)).fetchone()
                if pre_existing is None:
                    cursor.execute('INSERT INTO {tab} (exchange, keyword, '
                                   'destination) VALUES (?, ?, ?)'.format(
                        tab=self.TABLE_NAME), (name, keyword, destination))
                elif pre_existing[0] != destination:
                    cursor.execute('UPDATE {tab} SET destination=? WHERE '
                                   'exchange=? AND keyword=?'.format(
                        tab=self.TABLE_NAME), (destination, name, keyword))


class Secrets(Storage):
    TABLE_NAME = 'secrets'
    TABLE_SCHEMA = 'name TEXT PRIMARY KEY NOT NULL, value TEXT'

    def __getitem__(self, item):
        result = self._get_row('name', item, 'value')
        if result is None:
            raise KeyError('No known secret with name {!r}.'.format(item))
        return result[0]

    def __setitem__(self, key, value):
        with self.cursor as cursor:
            cursor.execute('REPLACE INTO {} VALUES (?, ?)'.format(self.TABLE_NAME), (key, value))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class Sessions(Storage):
    """Class to represent currently known sessions."""
    TABLE_NAME = 'sessions'
    TABLE_SCHEMA = ('id TEXT PRIMARY KEY NOT NULL, '
                    'curr_exchange TEXT NOT NULL, '
                    'data TEXT')

    def __iter__(self):
        """Iterate over the Sessions' IDs, current exchanges, and data (possibly None)."""
        return self._iterate_columns('id', 'curr_exchange', 'data')

    def get(self, session):
        """Get the state of a session.

        :param session: The session identifier.
        :returns: A 2-tuple containing (exchange, data). The value of data
            may be None.
        """
        retval = self._get_row('id', session, 'curr_exchange', 'data')
        if retval is None:
            return None, None
        return retval

    def delete(self, session):
        """Delete a particular session.

        :param session: The ID of thesession to delete.
        """
        self._remove('id', session)

    def set(self, session, exchange, data=None):
        """Set the state of a session.

        :param session: The session identifier.
        :param exchange: The session's current exchange.
        :param data: Any text data associated with the session.
        """
        with self.cursor as cursor:
            cursor.execute('REPLACE INTO {} VALUES (?, ?, ?)'.format(
                self.TABLE_NAME),
                (session, exchange, data))
