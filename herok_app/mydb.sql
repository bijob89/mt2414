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
