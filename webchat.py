import exchange_translation
from flask import Flask, render_template, request, redirect, url_for, Response

from process_chat import process_chat

app = Flask(__name__)


@app.route('/new_exchange', methods=['GET'])
def new_exchange():
    return render_template('new_exchange.html')


@app.route('/edit_exchange', methods=['GET'])
def edit_exchange():
    return render_template('new_exchange.html',
                           current_exchange=request.values.get('exchange'),
                           keywords=exchange_translation.keywords,
                           prompt=exchange_translation.prompt,
                           default=exchange_translation.default)


@app.route('/new_exchange', methods=['POST'])
def new_exchange_post():
    name = request.values.get('exchange-name', '')
    existing = request.values.get('existing')
    prompt = request.values.get('exchange-prompt', '')
    default = request.values.get('exchange-default', None)
    keywords = request.values.getlist('keyword')
    target_exchanges = request.values.getlist('exchange')
    keyword_map = {keyword.lower(): exchange
                   for keyword, exchange in zip(keywords, target_exchanges)
                   if keyword and exchange}

    if existing:
        exchange_translation.delete(existing)
    exchange_translation.save_to_disk(name, prompt, keyword_map, default)
    return redirect(url_for('exchanges'))


@app.route('/exchanges', methods=['GET'])
def exchanges():
    return render_template('exchanges.html',
                           exchanges=exchange_translation.all_exchanges(),
                           keywords=exchange_translation.keywords)


@app.route('/delete_exchange', methods=['POST'])
def delete_exchange():
    to_delete = request.values.get('exchange_name')
    if to_delete is not None:
        exchange_translation.delete(to_delete)
    return redirect(url_for('exchanges'))


@app.route('/chat', methods=['GET'])
def chat():
    return render_template('chat.html')


@app.route('/chat_message', methods=['POST'])
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


@app.route('/')
def redirect_root():
    return redirect(url_for('exchanges'))


if __name__ == '__main__':
    app.run(debug=True)
