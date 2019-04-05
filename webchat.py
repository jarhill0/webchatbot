from functools import wraps

from flask import Flask, Response, make_response, redirect, render_template, request, url_for

import exchange_translation
from process_chat import process_chat
from session_interface import all_logged_convos, all_sessions, clear_session as session_clear, get_log
from storage import Cookies, Secrets

app = Flask(__name__)

COOKIES = Cookies()
SECRETS = Secrets()


def remove_prefix(string, prefix):
    """Remove prefix from string and return it."""
    if string[:len(prefix)] != prefix:
        return string
    return string[len(prefix):]


def authenticated(route):
    """Wrap a function that needs to be authenticated."""

    @wraps(route)
    def auth_wrapper(*args, **kwargs):
        if 'auth' in request.cookies and COOKIES.check(request.cookies['auth']):
            return route(*args, **kwargs)
        return redirect(url_for('log_in', dest=remove_prefix(request.url, request.url_root)))

    return auth_wrapper


@app.route('/new_exchange', methods=['GET'])
@authenticated
def new_exchange():
    return render_template('new_exchange.html')


@app.route('/edit_exchange', methods=['GET'])
@authenticated
def edit_exchange():
    return render_template('new_exchange.html',
                           current_exchange=request.values.get('exchange'),
                           keywords=exchange_translation.keywords,
                           prompt=exchange_translation.prompt,
                           default=exchange_translation.default,
                           rank=exchange_translation.rank,
                           exchange_type=exchange_translation.exchange_type)


@app.route('/new_exchange', methods=['POST'])
@authenticated
def new_exchange_post():
    name = request.values.get('exchange-name', '')
    existing = request.values.get('existing')
    prompt = request.values.get('exchange-prompt', '')
    default = request.values.get('exchange-default', None)
    rank = request.values.get('exchange-rank', None)
    type_ = request.values.get('exchange-type', None)
    keywords = request.values.getlist('keyword')
    target_exchanges = request.values.getlist('exchange')
    if type_ == 'name':
        keyword_map = {'yes_name': request.values.get('yes_name', ''),
                       'no_name': request.values.get('no_name', '')}
    else:
        keyword_map = {keyword.lower(): exchange
                       for keyword, exchange in zip(keywords, target_exchanges)
                       if keyword and exchange}

    if existing:
        exchange_translation.delete(existing)
    exchange_translation.save_to_disk(name, prompt, keyword_map, default, rank, type_)
    return redirect(url_for('exchanges'))


@app.route('/exchanges', methods=['GET'])
@authenticated
def exchanges():
    return render_template('exchanges.html',
                           exchanges=exchange_translation.all_exchanges(),
                           keywords=exchange_translation.keywords)


@app.route('/delete_exchange', methods=['POST'])
@authenticated
def delete_exchange():
    to_delete = request.values.get('exchange_name')
    if to_delete is not None:
        exchange_translation.delete(to_delete)
    return redirect(url_for('exchanges'))


@app.route('/chat', methods=['GET'])
@authenticated
def chat():
    return render_template('chat.html')


@app.route('/chat_message', methods=['POST'])
@authenticated
def get_chat_message():
    body = request.get_json()
    session = body.get('session')
    if session is None:
        return Response('No session!', status=403)
    message = body.get('message')

    response = process_chat(session, message)
    if response is None:
        return '[silence]'
    return response


@app.route('/sessions', methods=['GET'])
@authenticated
def sessions():
    return render_template('sessions.html', sessions=all_sessions())


@app.route('/delete_session', methods=['POST'])
@authenticated
def clear_session():
    to_delete = request.values.get('session_id')
    if to_delete is not None:
        session_clear(to_delete)
    return redirect(url_for('sessions'))


@app.route('/logs', methods=['GET'])
@authenticated
def all_logs():
    return render_template('all_logs.html', logs=all_logged_convos())


@app.route('/viewlog', methods=['GET'])
@authenticated
def view_log():
    to_view = request.values.get('log')
    if to_view:
        return render_template('view_log.html', name=to_view, log=get_log(to_view))
    return redirect(url_for('all_logs'))


@app.route('/login', methods=['GET'])
def log_in():
    if 'auth' in request.cookies and COOKIES.check(request.cookies['auth']):
        return redirect(request.values.get('dest') or url_for('redirect_root'))

    COOKIES.prune()
    return render_template('auth.html', dest=request.values.get('dest', ''))


@app.route('/login', methods=['POST'])
def authenticate():
    if 'auth' in request.cookies and COOKIES.check(request.cookies['auth']):
        return redirect(request.values.get('dest') or url_for('redirect_root'))

    if request.values.get('password', '') == SECRETS['password']:
        resp = make_response(redirect(request.values.get('dest') or url_for('redirect_root')))
        resp.set_cookie('auth', COOKIES.new())
        return resp
    else:
        return render_template('auth.html', error='Incorrect password.', dest=request.values.get('dest', ''))


@app.route('/logout', methods=['POST'])
def log_out():
    cookie = request.cookies.get('auth')
    if cookie:
        COOKIES.remove(cookie)
    return redirect(url_for('log_in'))


@app.route('/')
def redirect_root():
    return redirect(url_for('exchanges'))


if __name__ == '__main__':
    app.run(debug=True)
