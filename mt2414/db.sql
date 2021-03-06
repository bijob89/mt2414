CREATE TABLE roles (
	id BIGSERIAL PRIMARY KEY,
	name TEXT UNIQUE NOT NULL
);

INSERT INTO roles (name) VALUES ('superadmin');
INSERT INTO roles (name) VALUES ('admin');
INSERT INTO roles (name) VALUES ('member');

CREATE TABLE users (
	id BIGSERIAL PRIMARY KEY,
	email TEXT UNIQUE NOT NULL,
	email_verified BOOLEAN DEFAULT FALSE,
	verification_code TEXT UNIQUE,
	password_hash BYTEA UNIQUE NOT NULL,
	password_salt BYTEA UNIQUE NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	role_id BIGINT REFERENCES roles(id) DEFAULT 3
);

CREATE TABLE keys (
	id BIGSERIAL PRIMARY KEY,
	access_id TEXT UNIQUE NOT NULL,
	key_hash BYTEA UNIQUE NOT NULL,
	key_salt BYTEA UNIQUE NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	user_id BIGINT REFERENCES users(id) NOT NULL
);

CREATE TABLE sources (
	id BIGSERIAL PRIMARY KEY,
	language TEXT NOT NULL,
	version VARCHAR NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone
);

CREATE TABLE sourcetexts (
	id BIGSERIAL PRIMARY KEY,
	book_name TEXT NOT NULL,
	content TEXT NOT NULL,
	revision_num TEXT NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL
);

CREATE TABLE cluster (
	id BIGSERIAL PRIMARY KEY,
	book_name TEXT,
	token TEXT,
	revision_num TEXT,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL
);


CREATE TABLE concordance (
	id BIGSERIAL PRIMARY KEY,
	pickledata BYTEA NOT NULL,
	source_id BIGINT REFERENCES sources(id) NOT NULL,
	revision_num INT NOT NULL
);

CREATE TABLE autogeneratedtokens (
	id BIGSERIAL PRIMARY KEY,
	token TEXT NOT NULL,
	targetlang TEXT,
	revision_num TEXT NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL
);

CREATE TABLE autotokentranslations (
	id BIGSERIAL PRIMARY KEY,
	token TEXT NOT NULL,
	translated_token TEXT,
	targetlang TEXT,
	revision_num TEXT NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL,
	pickledata BYTEA
);

CREATE TABLE taggedtokens (
	id BIGSERIAL PRIMARY KEY,
	token TEXT NOT NULL,
	strongs_num VARCHAR NOT NULL,
	tranlated_token TEXT,
	targetlang TEXT,
	revision_num TEXT NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL
);

CREATE TABLE translationtexts (
	id BIGSERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	content TEXT NOT NULL,
	language TEXT NOT NULL,
	revision_num TEXT NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL
);

CREATE TABLE targetlanglist (
	id BIGSERIAL PRIMARY KEY,
	picklelist BYTEA NOT NULL
);

