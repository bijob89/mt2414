CREATE TABLE users (
	id BIGSERIAL PRIMARY KEY,
	email TEXT UNIQUE NOT NULL,
	email_verified BOOLEAN DEFAULT FALSE,
	verification_code TEXT UNIQUE NOT NULL,
	password_hash BYTEA UNIQUE NOT NULL,
	password_salt BYTEA UNIQUE NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone
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
	version VARCHAR UNIQUE NOT NULL,
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

CREATE TABLE concordance (
	id BIGSERIAL PRIMARY KEY,
	token TEXT NOT NULL,
	book_name TEXT NOT NULL,
	concordances TEXT NOT NULL,
	revision_num TEXT NOT NULL,
	created_at timestamp with time zone,
	updated_at timestamp with time zone,
	deleted_at timestamp with time zone,
	source_id BIGINT REFERENCES sources(id) NOT NULL
);

CREATE TABLE tokenwords (
	id BIGSERIAL PRIMARY KEY,
	token TEXT NOT NULL,
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

