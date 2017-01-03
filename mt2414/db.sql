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
