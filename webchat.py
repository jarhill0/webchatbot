from functools import wraps
from re import compile, finditer
from string import digits

from flask import Flask, Response, jsonify, make_response, redirect, render_template, request, url_for
from twilio.twiml.messaging_response import Message, MessagingResponse
from werkzeug.datastructures import Headers

import exchange_translation
import tangent_interface
from process_chat import get_prompt, process_chat
from send_sms import send_message
from session_interface import all_logged_convos, all_sessions, clear_session as session_clear, get_log, get_session, \
    set_session
from storage import Cookies, Images, Secrets

app = Flask(__name__)

COOKIES = Cookies()
SECRETS = Secrets()
IMAGES = Images()

IMG_REGEX = compile(r'IMAGE\(([^)]+)\)')


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
    return render_template('new_exchange.html', name=request.values.get('name'))


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
    name = request.values.get('exchange-name', '').strip()
    existing = request.values.get('existing')
    prompt = request.values.get('exchange-prompt', '')
    default = request.values.get('exchange-default', None)
    rank = request.values.get('exchange-rank', None)
    type_ = request.values.get('exchange-type', None)
    keywords = request.values.getlist('keyword')
    target_exchanges = request.values.getlist('exchange')
    if type_ == 'name':
        keyword_map = {'yes_name': request.values.get('yes_name', '').strip(),
                       'no_name': request.values.get('no_name', '').strip()}
    else:
        keyword_map = {keyword.lower().strip(): exchange.strip()
                       for keyword, exchange in zip(keywords, target_exchanges)
                       if keyword and exchange}

    if existing:
        exchange_translation.delete(existing)
    exchange_translation.save_to_disk(name, prompt, keyword_map, default, rank, type_)
    return redirect(url_for('exchanges', _anchor=name))


@app.route('/exchanges', methods=['GET'])
@authenticated
def exchanges():
    all_exchanges = tuple(exchange_translation.all_exchanges())
    exch_names = set(exch[0] for exch in all_exchanges)
    return render_template('exchanges.html',
                           exchanges=all_exchanges,
                           keywords=exchange_translation.keywords,
                           exch_names=exch_names)


@app.route('/delete_exchange', methods=['POST'])
@authenticated
def delete_exchange():
    to_delete = request.values.get('exchange_name')
    if to_delete is not None:
        exchange_translation.delete(to_delete)
    return redirect(url_for('exchanges'))


@app.route('/duplicate_exchange', methods=['POST'])
@authenticated
def duplicate_exchange():
    old_name = request.values.get('old_name')
    new_name = request.values.get('new_name')
    if old_name and new_name:
        exchange_translation.duplicate(old_name, new_name)
    return redirect(url_for('edit_exchange', exchange=new_name))


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
        return ''
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


@app.route('/stepin', methods=['GET'])
@authenticated
def step_in():
    session_id = request.values.get('session')
    if session_id:
        exch, data = get_session(session_id)
        all_exchanges = tuple(exchange_translation.all_exchanges())
        return render_template('stepin.html', session_id=session_id, exchange=exch, session_data=data,
                               log=get_log(session_id), all_exchanges=all_exchanges)
    return redirect(url_for('sessions'))


@app.route('/sessions/new', methods=['GET'])
@authenticated
def new_session():
    all_exchanges = tuple(exchange_translation.all_exchanges())
    return render_template('new_session.html', all_exchanges=all_exchanges)


@app.route('/sessions/new', methods=['POST'])
@authenticated
def new_session_post():
    session_id = request.values.get('session-id')
    exchange = request.values.get('exchange')
    if not session_id or not exchange:
        return render_template('new_session.html', all_exchanges=tuple(exchange_translation.all_exchanges()),
                               error='Session ID and exchange are required!')
    all_digits = set(digits)
    id_digits = ''.join(d for d in session_id if d in all_digits)
    if len(id_digits) == 10:
        phone_num = '+1' + id_digits
    elif len(id_digits) == 11 and id_digits[0] == '1':
        phone_num = '+' + id_digits
    else:
        return render_template('new_session.html', all_exchanges=tuple(exchange_translation.all_exchanges()),
                               error='Bad phone number! (should be 10 digits)')
    send_prompt = request.values.get('send-prompt', 'on') == 'on'
    keys = request.values.getlist('data-key')
    values = request.values.getlist('data-value')
    user_data = dict(zip(keys, values))
    try:
        if user_data[''] == '':  # we don't want that
            del user_data['']
    except KeyError:
        pass
    set_session(phone_num, exchange, user_data)
    if send_prompt:
        prompt = get_prompt(phone_num, exchange, user_data)
        send_message_wrapper(phone_num, prompt)
    return redirect(url_for('new_session'))


@app.route('/send_message', methods=['POST'])
@authenticated
def send_manual_message():
    body = request.get_json()
    session = body.get('session')
    message = body.get('message')
    if message is None or session is None:
        return 'Message and session must be provided!', 400
    send_message_wrapper(session, message)
    return message


def send_message_wrapper(session, message):
    send_message(session, message, request.url, convert_to_twilio_outbound)


def convert_to_twilio_outbound(text_message, url_base):
    """Convert a message to a Twilio outbound message by doing image substitution.

    :param text_message: The message, as text, where IMAGE(name.png) represents the image name.png.
    :param url_base: The base URL of this website.
    :returns A dict to be used as kwargs and passed to Client.messages.create.
    """
    start_ind = 0
    text_only = []
    message_images = []
    for match in finditer(IMG_REGEX, text_message):
        match_start, match_end = match.span()
        text_only.append(text_message[start_ind:match_start].strip())
        message_images.append(url_base + url_for('image', name=match.group(1)))
        start_ind = match_end
    text_only.append(text_message[start_ind:])
    return {'text': ' '.join(text_only), 'images': message_images}


@app.route('/set_exchange', methods=['POST'])
@authenticated
def manual_set_exchange():
    body = request.get_json()
    session_id = body.get('session')
    new_exch = body.get('exchange')
    remove_queue = body.get('de_queue', False)
    send_prompt = body.get('send_prompt', False)
    if session_id is None or new_exch is None:
        return 'Session and exchange must be provided!', 400
    _, data = get_session(session_id)
    if remove_queue:
        data['queued'] = False
    if send_prompt:
        prompt = get_prompt(session_id, new_exch, data)
        send_message_wrapper(session_id, prompt)
    set_session(session_id, new_exch, data)
    return ''


@app.route('/delete_key', methods=['POST'])
@authenticated
def manual_delete_key():
    body = request.get_json()
    session_id = body.get('session')
    key = body.get('key')
    if session_id is None or key is None:
        return 'Session and key must be provided!', 400
    exchange, data = get_session(session_id)
    try:
        del data[key]
    except KeyError:
        pass
    set_session(session_id, exchange, data)
    return ''


@app.route('/update_key', methods=['POST'])
@authenticated
def manual_update_key():
    body = request.get_json()
    session_id = body.get('session')
    key = body.get('key')
    value = body.get('value')
    if None in (session_id, key, value):
        return 'Session, key and value must be provided!', 400
    exchange, data = get_session(session_id)
    data[key] = value
    set_session(session_id, exchange, data)
    return ''


@app.route('/stepin_poll', methods=['GET'])
@authenticated
def poll_for_stepin():
    session_id = request.values.get('session')
    last_poll = request.values.get('since')
    if session_id is None or last_poll is None:
        return 'Session and last poll must be provided!', 400
    try:
        last_poll = float(last_poll)
    except ValueError:
        return 'Last Poll is not a valid epoch float!', 400

    return jsonify(time_filter(get_log(session_id), last_poll))


def time_filter(log, after):
    return [items[:2] for items in log if items[2].timestamp() > after]  # filter by timestamp


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
        resp.set_cookie('auth', value=COOKIES.new(), max_age=int(COOKIES.VALID_LENGTH.total_seconds()))
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


@app.route('/twilio_sms', methods=['GET', 'POST'])
def sms_reply():
    """Respond to Twilio SMS."""
    session = request.values.get('From')
    message = request.values.get('Body', '')

    if session is None:
        return Response(status=400, response='Error. No phone number.')

    num_media = int(request.values.get('NumMedia', 0))
    media = []
    for i in range(num_media):
        media_key = 'MediaUrl{}'.format(i)
        url = request.values.get(media_key)
        media.append(url)
    message = ''.join('USER_IMAGE: {}\n'.format(url) for url in media) + message

    bot_response = process_chat(session, message)

    return str(convert_to_twilio(bot_response))


def convert_to_twilio(text_message):
    """Convert a message to a Twilio MessagingResponse by doing image substitution.

    :param text_message: The message, as text, where IMAGE(name.png) represents the image name.png.
    :returns A MessagingResponse.
    """
    resp = MessagingResponse()
    if not text_message:
        return resp
    twilio_message = Message()
    start_ind = 0
    for match in finditer(IMG_REGEX, text_message):
        match_start, match_end = match.span()
        twilio_message.body(text_message[start_ind:match_start].strip())
        twilio_message.media(url_for('image', name=match.group(1)))
        start_ind = match_end
    twilio_message.body(text_message[start_ind:])
    resp.append(twilio_message)
    return resp


@app.route('/image', methods=['GET'])
def image():
    """Get an image."""
    name = request.values.get('name')
    if not name:
        return Response(status=400, response='Error. No image name provided.')
    img_blob, img_mime = IMAGES.get(name)
    if not img_blob:
        return Response(status=400, response='Error. Unknown image {!r}.'.format(name))
    headers = Headers()
    headers.add('Content-Disposition', 'inline', filename=name)
    return Response(img_blob, mimetype=img_mime, headers=headers)


@app.route('/images', methods=['GET'])
@authenticated
def images():
    """View and edit images."""
    return render_template('images.html', images=IMAGES, success=request.values.get('success'),
                           error=request.values.get('error'))


def message_dict(**kwargs):
    """Make a dict containing only keys with truthy corresponding values."""
    return {k: v for k, v in kwargs.items() if v}


@app.route('/upload_img', methods=['POST'])
@authenticated
def upload_image():
    success, error = process_image()
    return redirect(url_for('images', **message_dict(success=success, error=error)))


@app.route('/del_img', methods=['POST'])
@authenticated
def delete_image():
    to_delete = request.values.get('image')
    if to_delete:
        IMAGES.remove(to_delete)
    return redirect(url_for('images', success='Deleted {!r}.'.format(to_delete)))


def process_image():
    """Process an uploaded image.

    :returns: (success, error)
    """
    if 'image' not in request.files:
        return '', 'No file provided.'
    image_file = request.files['image']
    if not image_file.filename:
        return '', 'Empty file.'
    mimetype = image_file.content_type
    if not mimetype.lower().split('/')[0] == 'image':
        return '', 'Not an image.'
    img_blob = image_file.read()
    img_name = request.values.get('image_name') or image_file.filename
    IMAGES.set(name=img_name, image=img_blob, mimetype=mimetype)
    return 'Successfully uploaded image {!r}.'.format(img_name), ''


@app.route('/tangents', methods=['GET'])
@authenticated
def tangents():
    return render_template('tangents.html', all_tangents=tangent_interface.all_tangents)


@app.route('/tangents/edit', methods=['GET'])
@authenticated
def edit_tangent():
    id_ = request.values.get('id')
    _, rank, tangent = tangent_interface.get_tangent(id_)
    return render_template('edit_tangent.html', id_=id_, rank=rank, tangent=tangent)


@app.route('/tangents/edit', methods=['POST'])
@authenticated
def edit_tangent_post():
    rank = request.values.get('rank')
    try:
        rank = int(rank)
    except ValueError:
        return 'Rank is not a number!', 400
    tangent = request.values.get('tangent')
    id_ = request.values.get('id')
    if tangent is None:
        return 'Tangent must be provided!', 400
    if not id_:
        id_ = None
    tangent_interface.set_tangent(rank, tangent, id_)
    return redirect(url_for('tangents'))


@app.route('/tangents/delete', methods=['POST'])
@authenticated
def delete_tangent():
    id_ = request.values.get('id')
    if id_:
        tangent_interface.delete_tangent(id_)
    return redirect(url_for('tangents'))


if __name__ == '__main__':
    app.run(debug=True)
