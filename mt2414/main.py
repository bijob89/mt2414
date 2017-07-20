import os
import uuid
import sqlite3
import json
import psycopg2
from functools import wraps
from datetime import datetime, timedelta
import datetime
import scrypt
import requests
import jwt
from flask import Flask, request, session, redirect
from flask import g
from flask_cors import CORS, cross_origin
import nltk
import polib
import re
import base64
import logging

logging.basicConfig(filename='API_logs.log', format='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

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
        logging.warning('Unregistered user \'%s\' login attempt unsuccessful' % email)
        return '{"success":false, "message":"Invalid email"}'
    cursor.execute("SELECT u.password_hash, u.password_salt, r.name FROM users u LEFT JOIN roles r ON u.role_id = r.id WHERE u.email = %s",(email,))
    rst = cursor.fetchone()
    if not rst:
        return '{"success":false, "message":"Email is not Verified"}'
    password_hash = rst[0].hex()
    password_salt = bytes.fromhex(rst[1].hex())
    password_hash_new = scrypt.hash(password, password_salt).hex()
    role = rst[2]
    if password_hash == password_hash_new:
        access_token = jwt.encode({'sub': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days = 1), 'role': role}, jwt_hs256_secret, algorithm='HS256')
        logging.warning('User \'' + str(email) + '\' logged in successfully')
        return '{"access_token": "%s", "role":"%s"}\n' % (access_token.decode('utf-8'), role)
    logging.warning('User \'' + str(email) + '\' login attempt unsuccessful: Incorrect Password')
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
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, verification_code, password_hash, password_salt, created_at) VALUES (%s, %s, %s, %s, current_timestamp)",(email, verification_code, password_hash, password_salt))
        cursor.close()
        connection.commit()
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        return '{"success":true, "message":"Verification Email Sent"}'
    else:
        return '{"success":false, "message":"Email Already Exists"}'

@app.route("/v1/resetpassword", methods = ["POST"])
def reset_password():
    email = request.form['email']
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT email from users WHERE email = %s", (email,))
    if not cursor.fetchone():
        return '{"success":false, "message":"Email has not yet been registered"}'
    else:
        headers = {"api-key": sendinblue_key}
        url = "https://api.sendinblue.com/v2.0/email"
        verification_code = str(uuid.uuid4()).replace("-","")
        body = '''Hi,<br/><br/>your request for resetting the password has been recieved. <br/>
        Your temporary password is %s. Enter your new password by opening this link:

        <a href="http://autographamt.com/forgotpassword">http://autographamt.com/forgotpassword</a>

        <br/><br/>The documentation for accessing the API is available at <a href="http://docs.mt2414.in">docs.mt2414.in</a>''' % (verification_code)
        payload = {
            "to": {email: ""},
            "from": ["noreply@autographamt.in","AutographaMT"],
            "subject": "AutographaMT - Password reset verification mail",
            "html": body,
            }
        cursor.execute("UPDATE users SET verification_code= %s WHERE email = %s", (verification_code, email))
        cursor.close()
        connection.commit()
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        return '{"success":true, "message":"Link to reset password has been sent to the registered mail ID"}\n'

@app.route("/v1/forgotpassword", methods = ["POST"])
def reset_password2():
    temp_password = request.form['temp_password']
    password = request.form['password']
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM users WHERE verification_code = %s AND email_verified = True", (temp_password,))
    rst = cursor.fetchone()
    if not rst:
        return '{"success":false, "message":"Invalid temporary password."}'
    else:
        email = rst[0]
        password_salt = str(uuid.uuid4()).replace("-","")
        password_hash = scrypt.hash(password, password_salt)
        cursor.execute("UPDATE users SET verification_code = %s, password_hash = %s, password_salt = %s, updated_at = current_timestamp WHERE email = %s", (None, password_hash, password_salt, email))
        cursor.close()
        connection.commit()
        return '{"success":true, "message":"Password has been reset. Login with the new password."}'

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
                'verify_sub': True,
                'verify_exp': True
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
    return redirect("http://autographamt.com/")

@app.route("/v1/createsources", methods=["POST"])
@check_token
def create_sources():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    connection = get_db()
    cursor = connection.cursor()
    auth = request.headers.get('Authorization', None)
    parts = auth.split()
    if len(parts) == 2:
        token = parts[1]
        options = {
            'verify_sub': True,
            'verify_exp': True
        }
        algorithm = 'HS256'
        leeway = timedelta(seconds=10)
        decoded = jwt.decode(token, jwt_hs256_secret, options=options, algorithms=[algorithm], leeway=leeway)
        user_role = decoded['role']
        if user_role == 'admin' or user_role == 'superadmin':
            cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s", (language, version))
            rst = cursor.fetchone()
            if not rst:
                cursor.execute("INSERT INTO sources (language, version) VALUES (%s, %s)", (language, version))
            else:
                return '{"success":false, "message":"Source already exists."}'
            cursor.close()
            connection.commit()
            return '{"success":true, "message":"New source has been created"}'
        else:
            return '{"success":false, "message":"You don\'t have permission to access this page"}'

@app.route("/v1/sourceslist", methods=["GET"])
@check_token
def sources_list():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id, language, version, id FROM sources")
    rst = cursor.fetchall()
    cursor.close()
    tr = {}
    if not rst:
        return '{"success":false, "message":"No Sources available. Create new sources."}'
    else:
        for item in rst:
            tr[item[0]] = [item[1], item[2]]
        return json.dumps(tr)

def tokenise(content):
    remove_punct = re.sub(r'([!"#$%&\\\'\(\)\*\+,\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])','', content)
    token_list = nltk.word_tokenize(remove_punct)
    token_set = set([x.encode('utf-8') for x in token_list])
    return token_set

@app.route("/v1/sourceid", methods = ["POST"])
@check_token
def sourceid():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s", (language, version))
    rst = cursor.fetchone()
    cursor.close()
    if rst:
        source_id = rst[0]
        return str(source_id)

@app.route("/v1/sources", methods=["POST"])
@check_token
def sources():
    req = request.get_json(True)
    content = req["content"]
    source_id = req["source_id"]
    auth = request.headers.get('Authorization', None)
    parts = auth.split()
    email_id = request.email
    if len(parts) == 2:
        token = parts[1]
        options = {
            'verify_sub': True,
            'verify_exp': True
        }
        algorithm = 'HS256'
        leeway = timedelta(seconds=10)
        decoded = jwt.decode(token, jwt_hs256_secret, options=options, algorithms=[algorithm], leeway=leeway)
        user_role = decoded['role']
        if user_role == 'admin' or user_role == 'superadmin':
            connection = get_db()
            cursor = connection.cursor()
            changes = []
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
                        logging.warning('User \'' + str(email_id) + '(' + str(user_role) + ')\' uploaded revised version of \'' + str(book_name) + '\'. Source Id: ' + str(source_id))
                        token_set = tokenise(text_file)
                        for t in token_set:
                            cursor.execute("INSERT INTO cluster (token, book_name, revision_num, source_id) VALUES (%s, %s, %s, %s)", (t.decode("utf-8"), book_name, revision_num, source_id))
                elif book_name not in books:
                    revision_num = 1
                    cursor.execute("INSERT INTO sourcetexts (book_name, content, source_id, revision_num) VALUES (%s, %s, %s, %s)", (book_name, text_file, source_id, revision_num))
                    logging.warning('User \'' + str(email_id) + '(' + str(user_role) + ')\' uploaded new book \'' + str(book_name) + '\'. Source Id: ' + str(source_id))
                    changes.append(book_name)
                    token_set = tokenise(text_file)
                    for t in token_set:
                        cursor.execute("INSERT INTO cluster (token, book_name, revision_num, source_id) VALUES (%s, %s, %s, %s)", (t.decode("utf-8"), book_name, revision_num, source_id))
        else:
            return '{"success":false, "message":"You are not authorized to view this page. Contact Administrator"}'
    else:
        raise TokenError('Invalid header', 'Access token required')
    cursor.close()
    connection.commit()
    if changes:
        return '{"success":true, "message":"Source has been uploaded successfully."}'
    else:
        logging.warning('User:' + str(email_id) + ', Source content upload failed as files already exists.')
        return '{"success":false, "message":"No Changes. Existing source is already up-to-date."}'

@app.route("/v1/get_languages", methods=["POST"])
@check_token
def availableslan():
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT s.language, s.version FROM sources s  LEFT JOIN sourcetexts st ON st.source_id = s.id")
    books=set()
    language = cursor.fetchall()
    if not language:
        return '{"success":false, "message":"No sources"}'
    else:
        for rst in range(0, len(language)):
            books.add(language[rst])
        mylist=list(books)
        cursor.close()
        return json.dumps(mylist)

@app.route("/v1/get_books", methods=["POST"])
@check_token
def availablesbooks():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT st.book_name, st.revision_num FROM sources s LEFT JOIN sourcetexts st ON st.source_id = s.id WHERE s.language = %s AND s.version = %s",(language, version))
    al = cursor.fetchall()
    books=[]
    if not al:
        return '{"success":false, "message":"No books available"}'
    else:
        for rst in range(0, len(al)):
            books.append(al[rst])
        cursor.close()
        return json.dumps(books)

@app.route("/v1/language", methods=["POST"])
@check_token
def language():
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT language FROM sources")
    language = cursor.fetchall()
    language_list = set()
    if not language:
        return '{"success":false, "message":"No Languages"}'
    else:
        for rst in language:
            language_list.add(rst[0])
        cursor.close()
        return json.dumps(list(language_list))

@app.route("/v1/version", methods=["POST"])
@check_token
def version():
    req = request.get_json(True)
    language = req["language"]
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT version FROM sources WHERE language = %s",(language,))
    version = cursor.fetchall()
    version_list = set()
    if not version:
        return '{"success":false, "message":"No version"}'
    else:
        for rst in version:
            version_list.add(rst[0])
        cursor.close()
        return json.dumps(list(version_list))

@app.route("/v1/revision", methods=["POST"])
@check_token
def revision():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT st.revision_num FROM sources s LEFT JOIN sourcetexts st ON st.source_id = s.id WHERE s.language = %s AND s.version = %s",(language, version))
    revision = cursor.fetchall()
    revision_list=[]
    if not revision:
        return '{"success":false, "message":"No books available"}'
    else:
        for rst in revision:
            revision_list.append(rst[0])
        cursor.close()
        return json.dumps(list(revision_list))

@app.route("/v1/book", methods=["POST"])
@check_token
def book():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    connection =get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT st.book_name FROM sources s LEFT JOIN sourcetexts st ON st.source_id = s.id WHERE s.language = %s AND s.version = %s AND revision_num = %s",(language, version, revision))
    books = cursor.fetchall()
    book_list=[]
    if not books:
        return '{"success":false, "message":"No books available"}'
    else:
        for rst in books:
            book_list.append(rst[0])
        cursor.close()
        return json.dumps(list(book_list))

@app.route("/v1/getbookwiseautotokens", methods=["POST"])
@check_token
def bookwiseagt():
    req = request.get_json(True)
    sourcelang = req["sourcelang"]
    version = req["version"]
    revision = req["revision"]
    books = req["books"]
    notbooks = req["nbooks"]
    targetlang = req["targetlang"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s",(sourcelang, version))
    source_id = cursor.fetchone()
    email_id = request.email
    if not source_id:
        return '{"success":false, "message":"Source is not available. Upload source."}'
    else:
        toknwords = []
        ntoknwords = []
        availablelan = []
        cursor.execute("SELECT book_name FROM cluster WHERE source_id =%s AND revision_num = %s",(source_id[0], revision))
        avlbk = cursor.fetchall()
        for i in avlbk:
            availablelan.append(i[0])
        b = set(books) - set(availablelan)
        c =set(notbooks) - set(availablelan)
        translatedtokenlist = []
        cursor.execute("SELECT  token FROM autotokentranslations WHERE translated_token IS NOT NULL AND revision_num = %s AND targetlang = %s AND source_id = %s",(revision, targetlang, source_id[0] ))
        translatedtoken = cursor.fetchall()
        for tk in translatedtoken:
            translatedtokenlist.append(tk[0])
        if  not b and not c:
            if books and not notbooks:
                for bkn in books:
                    cursor.execute("SELECT token FROM cluster WHERE source_id =%s AND revision_num = %s AND book_name = %s",(source_id[0], revision, bkn,))
                    tokens = cursor.fetchall()
                    for t in tokens:
                        toknwords.append(t[0])
                stoknwords = set(toknwords)
                cursor.close()
                logging.warning( 'User \'' +str(email_id) + '\' downloaded tokens from \'' + str(", ".join(books)) + '\' book/books')
                return json.dumps(list(stoknwords))
            elif books and notbooks:
                for bkn in books:
                    cursor.execute("SELECT token FROM cluster WHERE source_id =%s AND revision_num = %s AND book_name = %s",(source_id[0], revision, bkn,))
                    tokens = cursor.fetchall()
                    for t in tokens:
                        toknwords.append(t[0])
                for nbkn in notbooks:
                    cursor.execute("SELECT token FROM cluster WHERE source_id =%s AND revision_num = %s AND book_name = %s",(source_id[0], revision, nbkn,))
                    ntokens = cursor.fetchall()
                    for t in ntokens:
                        ntoknwords.append(t[0])
                stoknwords = set(toknwords) -  set(ntoknwords)
                output = stoknwords - set(translatedtokenlist)
                cursor.close()
                logging.warning( 'User \'' +str(email_id) + '\' downloaded tokens from \'' + str(", ".join(books)) + '\' excluding from \'' + str(", ".join(notbooks)) + '\' book/books')
                return json.dumps(list(output))
        elif b and c:
            logging.warning('User:\'' + str(email_id) + '\'. Token download failed, Source books:\'' + str(", ".join(list(b) + list(c))) +'\' not available')
            return '{"success":false, "message":" %s and %s is not available. Upload it."}'  %((list(b)),list(c))
        elif not b and c:
            logging.warning('User:\'' + str(email_id) + '\'. Token download failed, Source books:\'' + str(", ".join(list(c))) +'\' not available')
            return '{"success":false, "message":" %s is not available. Upload it."}'  %(list(c))
        elif not c and b:
            logging.warning('User:\'' + str(email_id) + '\'. Token download failed, Source books:\'' + str(", ".join(list(b))) +'\' not available')
            return '{"success":false, "message":" %s is not available. Upload it."}'  %((list(b)))

@app.route("/v1/autotokens", methods=["GET", "POST"])
@check_token
def autotokens():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s", (language, version))
    source_id = cursor.fetchone()
    if not source_id:
        return '{"success":false, "message":"Source not available. Upload source"}'
    else:
        cursor.execute("SELECT token FROM cluster WHERE source_id = %s AND revision_num = %s", (source_id[0], revision))
        token_set = cursor.fetchall()
        if not token_set:
            return '{"success":false, "message":"Not a valid revision number"}'
        token_set1 = set([token_set[i] for i in range(0, len(token_set))])
        tr = {}
        for t in token_set1:
            tr[str(t)] = "concord"
        cursor.close()
        return json.dumps(tr)

@app.route("/v1/tokenlist", methods=["POST"])
@check_token
def tokenlist():
    req = request.get_json(True)
    sourcelang = req["sourcelang"]
    version = req["version"]
    revision = req["revision"]
    targetlang = req["targetlang"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s",(sourcelang, version))
    source_id = cursor.fetchone()
    if not source_id:
        return '{"success":false, "message":"Source is not available. Upload source."}'
    else:
        cursor.execute("SELECT  st.book_name FROM sources s LEFT JOIN sourcetexts st ON st.source_id = s.id WHERE s.language = %s AND s.version = %s AND st.revision_num = %s",(sourcelang, version, revision))
        books = cursor.fetchall()
        cursor.execute("SELECT  token FROM autotokentranslations WHERE translated_token IS NOT NULL AND revision_num = %s AND targetlang = %s AND source_id = %s",(revision, targetlang, source_id[0]))
        translated_token = cursor.fetchall()
        cursor.execute("SELECT  token FROM autotokentranslations WHERE translated_token IS NULL AND revision_num = %s AND targetlang = %s AND source_id = %s",(revision, targetlang, source_id[0]))
        not_trantoken = cursor.fetchall()
        if not translated_token:
            return '{"success":false, "message":"Translated tokens are not available. Upload token translation ."}'
        else:
            token = []
            for tk in translated_token:
                token.append(tk[0])
            nottranslated = []
            for nt in not_trantoken:
                nottranslated.append(nt[0])
            token_list = []
            result = {}
            for bk in books:
                token_list = []
                cursor.execute("SELECT  token FROM cluster WHERE revision_num = %s AND source_id = %s AND book_name = %s",(revision, source_id[0], bk[0]))
                cluster_token = cursor. fetchall()
                for ct in cluster_token:
                    token_list.append(ct[0])
                output1 = set(token_list) - set(token)
                output2 = set(token_list) & set(not_trantoken)
                output = set(output1) | set(output2)
                result[bk[0]] = list(output)
            cursor.close()
            return json.dumps(result)

@app.route("/v1/tokencount", methods=["POST"])
@check_token
def tokencount():
    req = request.get_json(True)
    sourcelang = req["sourcelang"]
    version = req["version"]
    revision = req["revision"]
    targetlang = req["targetlang"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s",(sourcelang, version))
    source_id = cursor.fetchone()
    if not source_id:
        return '{"success":false, "message":"Source is not available. Upload source."}'
    else:
        cursor.execute("SELECT  st.book_name FROM sources s LEFT JOIN sourcetexts st ON st.source_id = s.id WHERE s.language = %s AND s.version = %s AND st.revision_num = %s",(sourcelang, version, revision ))
        books = cursor.fetchall()
        cursor.execute("SELECT  token FROM autotokentranslations WHERE translated_token IS NOT NULL AND revision_num = %s AND targetlang = %s AND source_id = %s",(revision, targetlang, source_id[0]))
        translated_token = cursor.fetchall()
        if not translated_token:
            return '{"success":false, "message":"Tokens is not available. Upload token translation ."}'
        else:
            token = []
            for tk in translated_token:
                token.append(tk[0])
            token_list = []
            result = {}
            for bk in books:
                token_list = []
                cursor.execute("SELECT  token FROM cluster WHERE revision_num = %s AND source_id = %s AND book_name = %s",(revision, source_id[0], bk[0]))
                cluster_token = cursor. fetchall()
                for ct in cluster_token:
                    token_list.append(ct[0])
                output = set(token_list) - set(token)
                count = len(list(output))
                result[bk[0]] = count
            cursor.close()
            return json.dumps(result)

@app.route("/v1/uploadtokentranslation", methods=["POST"])
@check_token
def upload_tokens_translation():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    tokenwords = req["tokenwords"]
    targetlang = req["targetlang"]
    changes = []
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s ", (language, version))
    source_id = cursor.fetchone()
    if not source_id:
        return '{"success":false, "message":"Unable to locate the language, version and revision number specified"}'
    cursor.execute("SELECT token FROM autotokentranslations WHERE source_id = %s AND revision_num = %s AND targetlang = %s", (source_id[0], revision, targetlang))
    transtokens = cursor.fetchall()
    if transtokens:
        token_list = []
        for i in transtokens:
            token_list.append(i[0])
        for k, v in tokenwords.items():
            if v:
                if k in token_list:
                    cursor.execute("UPDATE autotokentranslations SET translated_token = %s WHERE token = %s AND source_id = %s AND targetlang = %s AND revision_num = %s", (v, k, source_id[0], targetlang, revision))
                else:
                    cursor.execute("INSERT INTO autotokentranslations (token, translated_token, targetlang, revision_num, source_id) VALUES (%s, %s, %s, %s, %s)",(k, v, targetlang, revision, source_id[0]))
                changes.append(v)
        cursor.close()
        connection.commit()
    else:
        for k, v in tokenwords.items():
            if v:
                cursor.execute("INSERT INTO autotokentranslations (token, translated_token, targetlang, revision_num, source_id) VALUES (%s, %s, %s, %s, %s)",(k, v, targetlang, revision, source_id[0]))
                changes.append(v)
        cursor.close()
        connection.commit()
    if changes:
        logging.warning('User \'' + str(request.email) + '\' uploaded translation of tokens successfully')
        return '{"success":true, "message":"Token translation have been uploaded successfully"}'
    else:
        logging.warning('User \'' + str(request.email) + '\' upload of token translation unsuccessfully')
        return '{"success":false, "message":"Incorrect file format used to upload token translation"}'

@app.route("/v1/uploadtaggedtokentranslation", methods=["POST"])
@check_token
def upload_taggedtokens_translation():
    req = request.get_json(True)
    language = req["language"]
    tokenwords = req["tokenwords"]
    targetlang = req["targetlang"]
    version = req["version"]
    revision = req["revision"]
    connection = get_db()
    cursor = connection.cursor()
    for k,v in tokenwords.items():
        cursor.execute("INSERT INTO taggedtokens (token,strongs_num,language,version,revision_num) VALUES (%s,%s,%s,%s,%s)",(v,k,language,version,revision))
    cursor.close()
    connection.commit()
    return '{success:true, message:"Tagged token have been updated."}'

@app.route("/v1/emailslist", methods=["GET"])
@check_token
def emails_list():
    connection = get_db()
    cursor = connection.cursor()
    user_email = request.email
    auth = request.headers.get('Authorization', None)
    parts = auth.split()
    if len(parts) == 2:
        token = parts[1]
        options = {
            'verify_sub': True,
            'verify_exp': True
        }
        algorithm = 'HS256'
        leeway = timedelta(seconds=10)
        decoded = jwt.decode(token, jwt_hs256_secret, options=options, algorithms=[algorithm], leeway=leeway)
        user_role = decoded['role']
        if user_role == 'superadmin':
            cursor.execute("SELECT email FROM users")
            email_list = []
            for e in cursor.fetchall():
                email_list.append(e[0])
            email_list.remove(str(user_email))
            return json.dumps(email_list)
        else:
            return '{success:false, message:"You are not authorized to view this page. Contact Administrator"}'
    else:
        raise TokenError('Invalid Token', 'Works only on autographamt.com')

@app.route("/v1/superadminapproval", methods = ["POST"])
@check_token
def super_admin_approval():
    req = request.get_json(True)
    connection = get_db()
    cursor = connection.cursor()
    admin = req["admin"]
    email = req["email"]
    auth = request.headers.get('Authorization', None)
    parts = auth.split()
    if len(parts) == 2:
        token = parts[1]
        options = {
            'verify_sub': True,
            'verify_exp': True
        }
        algorithm = 'HS256'
        leeway = timedelta(seconds=10)
        decoded = jwt.decode(token, jwt_hs256_secret, options=options, algorithms=[algorithm], leeway=leeway)
        user_role = decoded['role']
        if user_role == 'superadmin' and admin == "True":
            cursor.execute("UPDATE users SET role_id = 2 WHERE email = %s",(email,))
            cursor.close()
            connection.commit()
            return '{"success":true, "message":" ' + str(email) + ' has been provided with Administrator privilege."}'
        elif user_role == 'superadmin' and admin == "False":
            cursor.execute("UPDATE users SET role_id = 3 WHERE email = %s",(email,))
            cursor.close()
            connection.commit()
            return '{"success":true, "message":"Administrator privileges has been removed of user: ' + str(email) + '."}'
        elif user_role != 'superadmin':
            return '{"success":false, "message":"You are not authorized to edit this page. Contact Administrator"}'
    return '{}\n'

@app.route("/v1/generateconcordance", methods=["POST"])
@check_token
def generate_concordance():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id from sources WHERE language = %s and version = %s", (language, version))
    source_id = cursor.fetchone()
    if not source_id:
        return '{"success":false, "message":"Unable to find sources. Upload source."}'
    else:
        cursor.execute("SELECT token from cluster WHERE source_id = %s", (source_id[0],))
        token_set = cursor.fetchall()
        cursor.execute("SELECT book_name, content, revision_num FROM sourcetexts WHERE source_id = %s", (source_id[0],))
        content = cursor.fetchall()
        changes = []
        content_text = []
        for b, c, r in content:
            book_name = (re.search('(?<=\id )\w+', c)).group(0)
            escape_char = re.sub(r'\v ','\\v ', c)
            for line in escape_char.split('\n'):
                if (re.search('(?<=\c )\d+', line)) != None:
                    chapter_no = (re.search('(?<=\c )\d+', line)).group(0)
                if (re.search(r'(?<=\\v )\d+', line)) != None:
                    verse_no = re.search(r'((?<=\\v )\d+)',line).group(0)
                    verse = re.search(r'(?<=)(\\v )(\d+ )(.*)',line).group(3)
                    ref = str(book_name) + " - " + str(chapter_no) + ":" + str(verse_no)
                    content_text.append((r, ref, verse))
        full_text_list = []
        for item in content_text:
            temp_text = " ".join(item)
            full_text_list.append(temp_text)
        full_text = "\n".join(full_text_list)
        for i in range(0, len(token_set)):
            token = token_set[i][0]
            if token:
                concord = re.findall('(.*' + str(token) + '.*)' , full_text)
                for line in concord:
                    line_split = re.search(r'(\d+)(\s)(.*\d+:\d+)(\s)(.*)', line)
                    ref_no = line_split.group(3)
                    verse = line_split.group(5)
                    revision_num = line_split.group(1)
                    cursor.execute("SELECT book_name FROM concordance WHERE token = %s AND source_id = %s AND revision_num = %s", (token, source_id[0], revision_num))
                    ref_book = cursor.fetchall()
                    db_book = [ref_book[x][0] for x in range(0,len(ref_book))]
                    if ref_no not in db_book:
                        cursor.execute("INSERT INTO concordance (token, book_name, concordances, revision_num, source_id) VALUES (%s, %s, %s, %s, %s)", (token, ref_no, verse, revision_num, source_id[0]))
                        changes.append(book_name)
        cursor.close()
        connection.commit()
        if changes:
            return '{"success":true, "message":"concordances created and stored in DB"}'
        else:
            return '{"success":false, "message":"No changes made. Concordances are already up-to-date"}'

@app.route("/v1/getconcordance", methods=["POST"])
@check_token
def get_concordance():
    req = request.get_json(True)
    language = req["language"]
    version = req["version"]
    revision = req["revision"]
    token = req["token"]
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id from sources WHERE language = %s AND version = %s", (language, version))
    source_id = cursor.fetchone()
    if not source_id:
        return '{"success":false, "message":"Source is not available. Upload it"}'
    else:
        cursor.execute("SELECT book_name, concordances FROM concordance WHERE token = %s AND source_id = %s AND revision_num = %s", (token, source_id[0], str(revision)))
        concord = cursor.fetchall()
        if not concord:
            return '{"success":false, "message":"Token is not available"}'
        con = {}
        for i in range(0, len(concord)):
            book = concord[i][0]
            concordances = concord[i][1]
            con[str(book)] = str(concordances)
        cursor.close()
        return json.dumps(con)


@app.route("/v1/translations", methods=["POST"])
@check_token
def translations():
    req = request.get_json(True)
    sourcelang = req["sourcelang"]
    targetlang = req["targetlang"]
    version = req["version"]
    revision = req["revision"]
    books = req["books"]
    changes = []
    changes1 = []
    if len(books) == 0:
        return '{"success":false, "message":"Select the books to be Translated."}'#, 417
    connection = get_db()
    cursor = connection.cursor()
    tokens = {}
    cursor.execute("SELECT id FROM sources WHERE language = %s AND version = %s",(sourcelang, version))
    rst = cursor.fetchone()
    if not rst:
        logging.warning('Translation draft generation unsuccessful as no books were selected by user \'' + str(request.email) + '\'')
        return '{"success":false, "message":"Source is not available. Upload it"}'#, 204
    else:
        source_id = rst[0]
        cursor.execute("SELECT token, translated_token FROM autotokentranslations WHERE targetlang = %s AND source_id = %s AND translated_token IS NOT NULL",(targetlang, source_id))
        for t, tr in cursor.fetchall():
            if tr:
                tokens[t] = tr
        tr = {}
        tag_check = ['~', '$','\q', '\ide', '\toc', '\mt', '\h', '2', '(', '_', '“', '5', '.', "'", ':', '%', '#', ')', 'a', '^', '’', '<', '{', '”', '।', '?', '|', 'b', ';', '-', ']', '`', '0', '[', '/', '"', '6', '1', '=', '8', '+', '*', '9', 'c', '@', '3', '!', '>', ',', '4', '\\', '‘', '7', '&', '}', '\\v', '\\c', '\\p', '\\s', '\\id']
        for book in books:
            cursor.execute("SELECT content FROM sourcetexts WHERE source_id = %s AND revision_num = %s and book_name = %s",(source_id, revision, book))
            source_content = cursor.fetchone()
            if source_content:
                out_text_lines = []
                book_name = (re.search('(?<=\id )\w+', source_content[0])).group(0)
                changes.append(book_name)
                hyphenated_words = re.findall(r'\w+-\w+', source_content[0])
                content = re.sub(r'([!"#$%&\'\(\)\*\+,\.\/:;<=>\?\@\[\]^_`{|\}~।\”\“\‘\’1234567890 ])',r' \1 ', source_content[0])
                for line in content.split("\n"):
                    line_words = nltk.word_tokenize(line)
                    new_line_words = []
                    for word in line_words:
                        if word not in tag_check:
                            new_line_words.append(tokens.get(word, " >>>"+str(word)+"<<<"))
                        else:
                            new_line_words.append(tokens.get(word, word))
                    out_line = " ".join(new_line_words)
                    out_text_lines.append(out_line)
                out_text = "\n".join(out_text_lines)
                for w in hyphenated_words:
                    word = " >>>"+str(w)+"<<<"
                    replace = tokens.get(w, " >>>"+str(w)+"<<<")
                    out_text = re.sub(r'' + str(word), str(replace), out_text)
                out_final = re.sub(r'\s?([!"#$%&\'\(\)\*\+,-\.\/:;<=>\?\@\[\]^_`{|\}~।\”\’ ])',r'\1', out_text)
                out_final = re.sub(r'([\‘\“])\s?', r'\1', out_final)
                out_final = re.sub(r'-\s', '-', out_final)
                out_final = re.sub(r'(\d+)\s(\d+)', r'\1\2', out_final)
                out_final = re.sub(r'\[ ', r' \[', out_final)
                out_final = re.sub(r'\( ', r' \(', out_final)
                out_final = re.sub(r'(\n\\rem.*)','', out_final)
                out_final = re.sub(r' >>>\\toc<<< ', r'\n\\toc', out_final)
                out_final = re.sub(r'\\ide .*','\\\\ide UTF-8', out_final)
                out_final = re.sub('(\\\\id .*)','\\id ' + str(book_name), out_final)
                tr[book_name] = out_final
            else:
                changes1.append(book)
        cursor.close()
        connection.commit()
        if changes:
            logging.warning('Translation draft successfully generated by user \'' + str(request.email) + '\'')
            return json.dumps(tr)
        else:
            logging.warning('Translation draft generation by user \'' + str(request.email) + '\' unsuccessful')
            return '{"success":false, "message":"' + ", ".join(changes1) + ' not available. Upload it to generate draft"}'#, 503

@app.route("/v1/corrections", methods=["POST"])
@check_token
def corrections():
    return '{}\n'

@app.route("/v1/suggestions", methods=["GET"])
@check_token
def suggestions():
    return '{}\n'
