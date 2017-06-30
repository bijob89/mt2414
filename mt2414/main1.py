import os
import uuid
import sqlite3
import json
import psycopg2
from functools import wraps
from datetime import datetime, timedelta
import scrypt
import requests
import jwt
from flask import Flask, request, session
from flask import g
from flask_cors import CORS, cross_origin
import nltk
import polib
import re
import base64


PO_METADATA = {
    'Project-Id-Version': '1.0',
    'Report-Msgid-Bugs-To': 'tfbfgroup@googlegroups.com',
    'POT-Creation-Date': '2007-10-18 14:00+0100',
    'PO-Revision-Date': '2007-10-18 14:00+0100',
    'Last-Translator': 'you <you@example.com>',
    'Language-Team': 'English <yourteam@example.com>',
    'MIME-Version': '1.0',
    'Content-Type': 'text/plain; charset=utf-8',
    'Content-Transfer-Encoding': '8bit',
}


app = Flask(__name__)
CORS(app)

sendinblue_key = os.environ.get("MT2414_SENDINBLUE_KEY")
jwt_hs256_secret = os.environ.get("MT2414_HS256_SECRET")
postgres_host = os.environ.get("MT2414_POSTGRES_HOST", "localhost")
postgres_port = os.environ.get("MT2414_POSTGRES_PORT", "5432")
postgres_user = os.environ.get("MT2414_POSTGRES_USER", "postgres")
postgres_password = os.environ.get("MT2414_POSTGRES_PASSWORD", "secret")
postgres_database = os.environ.get("MT2414_POSTGRES_DATABASE", "postgres")

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = psycopg2.connect(dbname=postgres_database, user=postgres_user, password=postgres_password, host=postgres_host, port=postgres_port)
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()


@app.route("/v1/auth", methods=["POST"])
def auth():
    email = request.form["username"]
    password = request.form["password"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM users WHERE  email = %s",(email,))
    est = cursor.fetchone()
    if not est:
        return '{"success":false, "message":"Invalid email"}'
    cursor.execute("SELECT password_hash, password_salt FROM users WHERE email = %s AND email_verified = True", (email,))
    rst = cursor.fetchone()
    if not rst:
        return '{"success":false, "message":"Email is not Verified"}'
    password_hash = rst[0].hex()
    password_salt = bytes.fromhex(rst[1].hex())
    password_hash_new = scrypt.hash(password, password_salt).hex()
    if password_hash == password_hash_new:
        access_token = jwt.encode({'sub': email}, jwt_hs256_secret, algorithm='HS256')
        return '{"access_token": "%s"}\n' % access_token.decode('utf-8')
    return '{"success":false, "message":"Incorrect Password"}'


@app.route("/v1/registrations", methods=["POST"])
def new_registration():
    email = request.form['email']
    password = request.form['password']
    headers = {"api-key": sendinblue_key}
    url = "https://api.sendinblue.com/v2.0/email"
    verification_code = str(uuid.uuid4()).replace("-","")
    body = '''Hi,<br/><br/>Thanks for your interest to use the MT2414 web service. <br/>
    You need to confirm your email by opening this link:

    <a href="https://api.mt2414.in/v1/verifications/%s">https://api.mt2414.in/v1/verifications/%s</a>

    <br/><br/>The documentation for accessing the API is available at <a href="http://docs.mt2414.in">docs.mt2414.in</a>''' % (verification_code, verification_code)
    payload = {
        "to": {email: ""},
        "from": ["noreply@mt2414.in","Mt. 24:14"],
        "subject": "MT2414 - Please verify your email address",
        "html": body,
        }
    connection = get_db()
    password_salt = str(uuid.uuid4()).replace("-","")
    password_hash = scrypt.hash(password, password_salt)


    cursor = connection.cursor()
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        return '{"success":false, "message":"Email Already Exists"}'
    else:
        cursor.execute("INSERT INTO users (email, verification_code, password_hash, password_salt, created_at) VALUES (%s, %s, %s, %s, current_timestamp)",
                (email, verification_code, password_hash, password_salt))
    cursor.close()
    connection.commit()
    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    return '{"success":true, "message":"Verification Email Sent"}'

@app.route("/v1/resetpassword", methods = ["POST"])
def reset_password():
    email = request.form['email']
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT email from users WHERE email = %s", (email,))
    if cursor.fetchone():
        headers = {"api-key": sendinblue_key}
        url = "https://api.sendinblue.com/v2.0/email"
        verification_code = str(uuid.uuid4()).replace("-","")
        body = '''Hi,<br/><br/>your request for resetting the password has been recieved. <br/>
        Enter your new password by opening this link:

        <a href="https://api.mt2414.in/v1/forgotpassword/%s">https://api.mt2414.in/v1/forgotpassword/%s</a>

        <br/><br/>The documentation for accessing the API is available at <a href="http://docs.mt2414.in">docs.mt2414.in</a>''' % (verification_code, verification_code)
        payload = {
            "to": {email: ""},
            "from": ["noreply@mt2414.in","Mt. 24:14"],
            "subject": "MT2414 - Password reset verification mail",
            "html": body,
            }
        cursor.execute("UPDATE users SET verification_code= %s WHERE email = %s", (verification_code, email))
        cursor.close()
        connection.commit()
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
    else:
        return '{"success":false, "message":"Email has not yet been registered"}'
    return '{"success":true, "message":"Link to reset password has been sent to the registered mail ID"}\n'

@app.route("/v1/forgotpassword/<string:code>", methods = ["POST"])
def reset_password2(code):
    password = request.form['password']
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM users WHERE verification_code = %s AND email_verified = True", (code,))
    rst = cursor.fetchone()
    email = rst[0]
    password_salt = str(uuid.uuid4()).replace("-","")
    password_hash = scrypt.hash(password, password_salt)
    cursor.execute("UPDATE users SET verification_code = %s, password_hash = %s, password_salt = %s, created_at = current_timestamp WHERE email = %s", (code, password_hash, password_salt, email))
    cursor.close()
    connection.commit()
    return '{"success":true, "message":"Password has been reset"}\n'

class TokenError(Exception):

    def __init__(self, error, description, status_code=401, headers=None):
        self.error = error
        self.description = description
        self.status_code = status_code
        self.headers = headers

    def __repr__(self):
        return 'TokenError: %s' % self.error

    def __str__(self):
        return '%s. %s' % (self.error, self.description)

@app.errorhandler(TokenError)
def auth_exception_handler(error):
    return 'Authentication Failed\n', 401

def check_token(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        auth_header_value = request.headers.get('Authorization', None)
        if not auth_header_value:
            raise TokenError('No Authorization header', 'Token missing')

        parts = auth_header_value.split()

        if (len(parts) == 1) and (parts[0].lower() != 'bearer'):
            access_id, key = parts[0].split(":")
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute("SELECT keys.key_hash, keys.key_salt, users.email FROM keys LEFT JOIN users ON keys.user_id = users.id WHERE keys.access_id = %s AND users.email_verified = True", (access_id,))
            rst = cursor.fetchone()
            if not rst:
                raise TokenError('Invalid token', 'Invalid token')
            key_hash = rst[0].hex()
            key_salt = bytes.fromhex(rst[1].hex())

            key_hash_new = scrypt.hash(key, key_salt).hex()
            if key_hash == key_hash_new:
                request.email = rst[2]
            else:
                raise TokenError('Invalid token', 'Invalid token')
        elif (len(parts) == 2) and (parts[0].lower() == 'bearer'):
            # check for JWT token
            token = parts[1]
            options = {
                'verify_sub': True
            }
            algorithm = 'HS256'
            leeway = timedelta(seconds=10)

            try:
                decoded = jwt.decode(token, jwt_hs256_secret, options=options, algorithms=[algorithm], leeway=leeway)
                request.email = decoded['sub']
            except jwt.exceptions.DecodeError as e:
                raise TokenError('Invalid token', str(e))
        else:
            raise TokenError('Invalid header', 'Token contains spaces')

        #raise TokenError('Invalid JWT header', 'Token missing')
        return f(*args, **kwds)
    return wrapper

@app.route("/v1/keys", methods=["POST"])
@check_token
def new_key():
    key = str(uuid.uuid4()).replace("-","")
    access_id = str(uuid.uuid4()).replace("-","")
    key_salt = str(uuid.uuid4()).replace("-","")
    key_hash = scrypt.hash(key, key_salt)

    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM keys LEFT JOIN users ON keys.user_id = users.id WHERE users.email = %s AND users.email_verified = True", (request.email,))
    rst = cursor.fetchone()
    cursor.execute("SELECT id FROM users WHERE email = %s", (request.email,))
    rst2 = cursor.fetchone()
    user_id = rst2[0]
    if rst:
        cursor.execute("UPDATE keys SET access_id=%s, key_hash=%s, key_salt=%s WHERE user_id=%s", (access_id, key_hash, key_salt, user_id))
    else:
        cursor.execute("INSERT INTO keys (access_id, key_hash, key_salt, user_id) VALUES (%s, %s, %s, %s)", (access_id, key_hash, key_salt, user_id))
    cursor.close()
    connection.commit()
    return '{"id": "%s", "key": "%s"}\n' % (access_id, key)

@app.route("/v1/verifications/<string:code>", methods=["GET"])
def new_registration2(code):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM users WHERE verification_code = %s AND email_verified = False", (code,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET email_verified = True WHERE verification_code = %s", (code,))
    cursor.close()
    connection.commit()
    return '{"success":true, "message":"Email Verified"}'

@app.route("/v1/getemail1", methods = ["GET"])
@check_token
def get_email():
    return request.email

@app.route("/v1/sources", methods=["POST"])
@check_token
def sources():
    req = request.get_json(True)
    language = req["language"]
    content = req["content"]
    version = req["version"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id from sources WHERE language = %s and version = %s",(language, version))
    try:
        rst = cursor.fetchone()
    except:
        pass
    cursor.close()
    changes = []
    if rst:
        cursor = connection.cursor()
        source_id = rst[0]
        books = []
        cursor.execute("SELECT book_name, content, revision_num from sourcetexts WHERE source_id = %s", (source_id,))
        all_books = cursor.fetchall()
        for i in range(0, len(all_books)):
            books.append(all_books[i][0])
        for files in content:
            base_convert = ((base64.b64decode(files)).decode('utf-8')).replace('\r','')
            book_name = (re.search('(?<=\id )\w{3}', base_convert)).group(0)
            text_file = re.sub(r'(\n\\rem.*)','', base_convert)
            text_file = re.sub('(\\\\id .*)','\\id ' + str(book_name), text_file)
            if book_name in books:
                count = 0
                count1 = 0
                for i in range(0, len(all_books)):
                    if all_books[i][1] != text_file and book_name == all_books[i][0]:
                        count = count + 1
                    elif all_books[i][1] == text_file and book_name == all_books[i][0]:
                        count1 = all_books[i][2]
                if count1 == 0 and count != 0:
                    revision_num = count + 1
                    cursor.execute("INSERT INTO sourcetexts (book_name, content, source_id, revision_num) VALUES (%s, %s, %s, %s)", (book_name, text_file, source_id, revision_num))
                    changes.append(book_name)
                    text_file = re.sub(r'\\p ', '', text_file)
                    text_file = re.sub(r'\\v ', '', text_file)
                    text_file = re.sub(r'\\p\n', '', text_file)
                    text_file = re.sub(r'\\s .*', '', text_file)
                    text_file = re.sub(r'\n\n', '\n', text_file)
                    split = text_file.split("\c ")
                    split.pop(0)
                    for c in split:
                        new_text = c.split('\n')
                        chapter_no = new_text.pop(0)
                        new_text.remove("")
                        for v in new_text:
                            verse = book_name + " - " + str(chapter_no) + ":" + v
                            # print (verse)
                            cursor.execute("INSERT INTO sourcetexts1 (verse, source_id, revision_num) VALUES (%s, %s, %s)", (verse, source_id, revision_num))
                    remove_punct = re.sub(r'([!"#$%&\\\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])',r' \1 ', text_file)
                    remove_punct1 = re.sub(r'([!"#$%&\\\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])','', remove_punct)
                    token_list = nltk.word_tokenize(remove_punct1)
                    ignore = [ book_name, "SA", " QA", " CH", " CO", " id", " d", " PE", " TH", " KI", " TI", " i", " JN", " l", " m", " JN", " q", " qa"]
                    token_set = set([x.encode('utf-8') for x in token_list])
                    for t in token_set:
                        cursor.execute("INSERT INTO cluster (token, book_name, revision_num, source_id) VALUES (%s, %s, %s, %s)", (t.decode("utf-8"), book_name, revision_num, source_id))
            elif book_name not in books:
                revision_num = 1
                cursor.execute("INSERT INTO sourcetexts (book_name, content, source_id, revision_num) VALUES (%s, %s, %s, %s)", (book_name, text_file, source_id, revision_num))
                changes.append(book_name)
                text_file = re.sub(r'\\p ', '', text_file)
                text_file = re.sub(r'\\v ', '', text_file)
                text_file = re.sub(r'\\p\n', '', text_file)
                text_file = re.sub(r'\\s .*', '', text_file)
                text_file = re.sub(r'\n\n', '\n', text_file)
                split = text_file.split("\c ")
                split.pop(0)
                for c in split:
                    new_text = c.split('\n')
                    chapter_no = new_text.pop(0)
                    new_text.remove("")
                    for v in new_text:
                        verse = book_name + " - " + str(chapter_no) + ":" + v
                        # print (verse)
                        cursor.execute("INSERT INTO sourcetexts1 (verse, source_id, revision_num) VALUES (%s, %s, %s)", (verse, source_id, revision_num))
                remove_punct = re.sub(r'([!"#$%&\\\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])',r' \1 ', text_file)
                remove_punct1 = re.sub(r'([!"#$%&\\\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])','', remove_punct)
                token_list = nltk.word_tokenize(remove_punct1)
                ignore = [ book_name, "SA", " QA", " CH", " CO", " id", " d", " PE", " TH", " KI", " TI", " i", " JN", " l", " m", " JN", " q", " qa"]
                token_set = set([x.encode('utf-8') for x in token_list])
                for t in token_set:
                    cursor.execute("INSERT INTO cluster (token, book_name, revision_num, source_id) VALUES (%s, %s, %s, %s)", (t.decode("utf-8"), book_name, revision_num, source_id))
        cursor.close()
        connection.commit()
        if changes:
            return '{"success":true, "message":"Existing source updated"}'
        else:
            return '{"success":false, "message":"No Changes. Existing source is already up-to-date."}'
    else:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO sources (language, version) VALUES (%s , %s) RETURNING id", (language, version))
        source_id = cursor.fetchone()[0]
        verse_list = []
        for files in content:

            base_convert = ((base64.b64decode(files)).decode('utf-8')).replace('\r','')
            book_name = (re.search('(?<=\id )\w{3}', base_convert)).group(0)
            text_file = re.sub(r'(\n\\rem.*)','', base_convert)
            text_file = re.sub('(\\\\id .*)','\\id ' + str(book_name), text_file)
            revision_num = 1
            cursor.execute("INSERT INTO sourcetexts (book_name, content, revision_num, source_id) VALUES (%s, %s, %s, %s)", (book_name, text_file, revision_num, source_id))
            text_file = re.sub(r'\\p ', '', text_file)
            text_file = re.sub(r'\\v ', '', text_file)
            text_file = re.sub(r'\\p\n', '', text_file)
            text_file = re.sub(r'\\s .*', '', text_file)
            text_file = re.sub(r'\n\n', '\n', text_file)
            split = text_file.split("\c ")
            split.pop(0)
            for c in split:
                new_text = c.split('\n')
                chapter_no = new_text.pop(0)
                new_text.remove("")
                # new_text.remove("\n")
                for v in new_text:
                    verse = book_name + " - " + str(chapter_no) + ":" + v
                    verse_list.append(verse)
                    # print (verse)
                    # cursor.execute("INSERT INTO sourcetexts1 (verse, source_id, revision_num) VALUES (%s, %s, %s)", (verse, source_id, revision_num))

            remove_punct = re.sub(r'([!"#$%&\\\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])',r' \1 ', text_file)
            remove_punct1 = re.sub(r'([!"#$%&\\\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])','', remove_punct)
            token_list = nltk.word_tokenize(remove_punct1)
            ignore = [ book_name, "SA", " QA", " CH", " CO", " id", " d", " PE", " TH", " KI", " TI", " i", " JN", " l", " m", " JN", " q", " qa"]
            token_set = set([x.encode('utf-8') for x in token_list])
            for t in token_set:
                cursor.execute("INSERT INTO cluster (token, book_name, revision_num, source_id) VALUES (%s, %s, %s, %s)", (t.decode("utf-8"), book_name, revision_num, source_id))
        verse_set = "\n".join(verse_list)
        cursor.execute("INSERT INTO sourcetextsconcord (book_name, verse, source_id, revision_num) VALUES (%s, %s, %s, %s)",(book_name, verse_set, source_id, revision_num))
        cursor.close()
        connection.commit()
        return '{"success":true, "message":"New source added to database"}'



@app.route("/v1/get_languages", methods=["POST"])
@check_token
def availableslan():
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT s.language, s.version FROM sources s  LEFT JOIN sourcetexts st ON st.source_id = s.id")
    books=set()
    al = cursor.fetchall()
    for rst in range(0, len(al)):
        books.add(al[rst])
    mylist=list(books)
    return json.dumps(mylist)
    cursor.close()


@app.route("/v1/getbookwiseautotokens", methods=["POST"])
@check_token
def bookwiseagt():
    req = request.get_json(True)
    sourcelang = req["sourcelang"]
    version = req["version"]
    revision = req["revision"]
    books = req["books"]
    notbooks = req["nbooks"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s",(sourcelang, version))
    try:
        source_id = cursor.fetchone()[0]
    except:
        return '{"success":false, "message":"Source is not available. Upload source."}'
    toknwords = []
    ntoknwords = []
    availablelan = []
    cursor.execute("SELECT book_name FROM cluster WHERE source_id =%s AND revision_num = %s",(source_id, revision))
    avlbk = cursor.fetchall()
    for i in avlbk:
        availablelan.append(i[0])
    b = set(books) - set(availablelan)
    c =set(notbooks) - set(availablelan)
    cursor.execute("SELECT token FROM cluster WHERE source_id = %s AND revision_num = %s", (source_id, revision))
    token_set = cursor.fetchall()
    if not token_set:
        return '{"success":false, "message":"Not a valid revision number"}'
    if  not b and not c:
        if books and not notbooks:
            for bkn in books:
                cursor.execute("SELECT token FROM cluster WHERE source_id =%s AND revision_num = %s AND book_name = %s",(source_id, revision, bkn,))
                tokens = cursor.fetchall()
                for t in tokens:
                    toknwords.append(t[0])
            stoknwords = set(toknwords)
            # cursor.close()
            tr = {}
            for i in list(stoknwords):
                token = i[0]
                cursor.execute("SELECT concordances FROM concordance WHERE token = %s AND source_id = %s AND revision_num = %s", (token, source_id, revision))
                try:
                    concordance = cursor.fetchall()
                except:
                    pass
                # concordance_set = cursor.fetchall()
                # concordance_list = []
                # for i in range(0, len(concordance_set)):
                #     concordance = concordance_set[i][0] + " " + concordance_set[i][1]
                #     concordance_list.append(concordance)
                # concord = "\n".join(concordance_list)
                if concordance:
                    tr[i] = concordance[0][0]
            return json.dumps(tr)
            # return json.dumps(tr)
        elif books and notbooks:
            for bkn in books:
                cursor.execute("SELECT token FROM cluster WHERE source_id =%s AND revision_num = %s AND book_name = %s",(source_id, revision, bkn,))
                tokens = cursor.fetchall()
                for t in tokens:
                    toknwords.append(t[0])
            for nbkn in notbooks:
                cursor.execute("SELECT token FROM cluster WHERE source_id =%s AND revision_num = %s AND book_name = %s",(source_id, revision, nbkn,))
                ntokens = cursor.fetchall()
                for t in ntokens:
                    ntoknwords.append(t[0])
            stoknwords = set(toknwords) -  set(ntoknwords)
            # cursor.close()
            tr = {}
            tr = {}
            for i in list(stoknwords):
                # token = i[0]
                # cursor.execute("SELECT book_name, concordances FROM concordance WHERE token = %s AND source_id = %s AND revision_num = %s", (token, source_id, revision))
                # concordance_set = cursor.fetchall()
                # concordance_list = []
                # for i in range(0, len(concordance_set)):
                #     concordance = concordance_set[i][0] + " " + concordance_set[i][1]
                #     concordance_list.append(concordance)
                # concord = "\n".join(concordance_list)
                tr[i] = "concord"
            return json.dumps(tr)
    else:
        return '{"success":false, "message":" %s and %s is not available. Upload it."}'  %((list(b)),list(c))


@app.route("/v1/get_books", methods=["POST"])
@check_token
def availablesbooks():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT st.book_name, st.revision_num FROM sources s LEFT JOIN sourcetexts st ON st.source_id = s.id WHERE s.language = %s AND s.version = %s",(language, version))
    books=[]
    al = cursor.fetchall()
    for rst in range(0, len(al)):
        books.append(al[rst])
    return json.dumps(books)
    cursor.close()

@app.route("/v1/autotokens", methods=["GET", "POST"])
@check_token
def autotokens():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id from sources WHERE language = %s AND version = %s", (language, version))
    try:
        source_id = cursor.fetchone()[0]
    except:
        return '{"success":false, "message":"Language and version combination not found"}'
    cursor.execute("SELECT token FROM autogeneratedtokens WHERE source_id = %s AND revision_num = %s", (source_id, revision))
    tokens = cursor.fetchall()
    if not tokens:
        return '{"success":false, "message":"Not a valid revision number"}'
    #
    token_set = set([tokens[i] for i in range(0, len(tokens))])
    tr = {}
    # agt = []
    for t in token_set:
        tr[str(t)] = "concord"
    cursor.close()
    return json.dumps(tr)

@app.route("/v1/uploadtokentranslation", methods=["POST"])
@check_token
def upload_tokens_translation():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    tokenwords = req["tokenwords"]
    targetlang = req["targetlang"]
    connection = get_db()
    cursor = connection.cursor()
    changes = []
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s ", (language, version))
    try:
        source_id = cursor.fetchone()[0]
    except:
        return '{"success":false, "message":"Unable to locate the language, version and revision number specified"}'
    cursor.execute("SELECT token FROM autogeneratedtokens WHERE source_id = %s AND revision_num = %s", (source_id, revision))
    token_set = []
    for i in cursor.fetchall():
        token_set.append(i[0])
    if tokenwords:
        cursor.execute("SELECT token from autotokentranslations WHERE source_id = %s AND revision_num = %s AND targetlang = %s", (source_id, revision, targetlang))
        if cursor.fetchall():
            for k, v in tokenwords.items():
                if v and k in token_set:
                    cursor.execute("SELECT token from autotokentranslations WHERE token = %s AND source_id = %s AND revision_num = %s AND targetlang = %s", (k, source_id, revision, targetlang))
                    if cursor.fetchone():
                        cursor.execute("UPDATE autotokentranslations SET translated_token = %s WHERE token = %s AND source_id = %s AND targetlang = %s AND revision_num = %s", (v, k, source_id, targetlang, revision))
                        changes.append(k)
                    else:
                        cursor.execute("INSERT INTO autotokentranslations (token, translated_token, targetlang, revision_num, source_id) VALUES (%s, %s, %s, %s, %s)",(k, v, targetlang, revision, source_id))
                        changes.append(k)
        else:
            cursor.execute("SELECT token FROM autogeneratedtokens WHERE source_id = %s AND revision_num = %s", (source_id, revision))
            token_set = cursor.fetchall()
            for i in range(0, len(token_set)):
                token = str(token_set[i][0])
                translated_token = tokenwords.get(token, None)
                cursor.execute("INSERT INTO autotokentranslations (token, translated_token, targetlang, revision_num, source_id) VALUES (%s, %s, %s, %s, %s)", (token, translated_token, targetlang, str(revision), source_id))
                changes.append(token)
        cursor.close()
        connection.commit()
        if changes:
            return '{"success":true, "message":"Token translations have been updated."}'
        else:
            return '{"success":false, "message":"No Changes. Token translations are already up-to-date."}'
    else:
        return '{"success":false, "message":"File is Empty. Upload file with tokens and translations"}'

@app.route("/v1/generateconcordance", methods=["POST"])
@check_token
def get_concordance():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = "1"
    book_name = "Book"
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id from sources WHERE language = %s and version = %s", (language, version))
    try:
        source_id = cursor.fetchone()[0]
    except:
        return '{"success":false, "message":"Unable to find sources. Upload source."}'
    cursor.execute("SELECT token from cluster WHERE source_id = %s AND revision_num = %s", (source_id,revision))
    tokens = []
    for i in cursor.fetchall():
        tokens.append(i[0])
    token_set = set(tokens)
    cursor.execute("SELECT verse FROM sourcetextsconcord WHERE source_id = %s AND revision_num = %s",(source_id, revision))
    verses = cursor.fetchone()[0]
    # verse_list = []
    # for i in verses:
    #     verse_list.append(i[0])
    # verse_set = "\n".join(verse_list)
    tr = {}
    changes = []
    # cursor.execute("SELECT conc")
    for t in token_set:
        concord = re.findall('(.*' + str(t) + '.*)' , verses)
        concordance = "\n".join(concord)
        cursor.execute("INSERT INTO concordance (token, concordances, book_name, source_id, revision_num) VALUES (%s, %s, %s, %s, %s)", (t, concordance, book_name, source_id, revision))
        changes.append(t)
    cursor.close()
    connection.commit()
    if changes:
        return '{"success":true, "message":"concordances created and stored in DB"}'
    else:
        return '{"success":false, "message":"No changes made. Concordances are already up-to-date"}'

@app.route("/v1/getconcordance", methods=["POST"])
@check_token
def generate_concordance():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    token = req["token"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id from sources WHERE language = %s AND version = %s", (language, version))
    source_id = cursor.fetchone()[0]
    cursor.execute("SELECT book_name, concordances FROM concordance WHERE token = %s AND source_id = %s AND revision_num = %s", (token, source_id, str(revision)))
    concord = cursor.fetchall()
    if not concord:
        return '{"success":false, "message":"Token is not available"}'
    cursor.close()
    con = {}
    for i in range(0, len(concord)):
        book = concord[i][0]
        concordances = concord[i][1]
        con[str(book)] = str(concordances)
    return json.dumps(con)

@app.route("/v1/translations", methods=["POST"])
@check_token
def translations():
    req = request.get_json(True)
    sourcelang = req["sourcelang"]
    targetlang = req["targetlang"]
    version = req["version"]
    revision = req["revision"]
    connection = get_db()
    cursor = connection.cursor()
    tokens = {}
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s",(sourcelang, version))
    try:
        source_id = cursor.fetchone()[0]
    except:
        return '{"success":false, "message":"Source is not available. Upload source."}'
    cursor.execute("SELECT token, translated_token FROM autogeneratedtokens WHERE targetlang = %s AND source_id = %s AND translated_token IS NOT NULL",(targetlang, source_id))
    for t, tr in cursor.fetchall():
        if tr:
            tokens[t] = tr
    cursor.execute("SELECT book_name, content FROM sourcetexts WHERE source_id = %s AND revision_num = %s", (source_id, revision))
    out = []
    for rst in cursor.fetchall():
        out.append((rst[0], rst[1]))
    tr = {}
    for name, book in out:
        out_text_lines = []
        content = re.sub(r'([!"#$%&\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~। ])',r' \1 ', book)
        for line in content.split("\n"):
            line_words = nltk.word_tokenize(line)
            new_line_words = []
            for word in line_words:
                new_line_words.append(tokens.get(word, word))
            out_line = " ".join(new_line_words)
            out_text_lines.append(out_line)

        out_text = "\n".join(out_text_lines)
        out_final = re.sub(r'\s?([!"#$%&\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~। ])',r'\1', out_text)
        out_text_file = re.sub('(?s).*?(\\c 1)', '\\id ' + str(book_name) + ' AutographaMT Translation ' + str(sourcelang)+ ' to ' + str(targetlang) +'\n\n\\1', out_final, 1)
        tr[name] = out_text_file
        cursor.execute("INSERT INTO translationtexts (name, content, language, revision_num, source_id) VALUES (%s, %s, %s, %s, %s)", (name, out_text_file, targetlang, revision, source_id))
    cursor.close()
    connection.commit()
    return json.dumps(tr)

@app.route("/v1/corrections", methods=["POST"])
@check_token
def corrections():
    return '{}\n'


@app.route("/v1/suggestions", methods=["GET"])
@check_token
def suggestions():
    return '{}\n'
