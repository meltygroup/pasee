CREATE DATABASE pasee;
CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS groups(name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS user_in_group(
    username TEXT references users(username),
    group_name TEXT references groups(name),
    PRIMARY KEY(username, group_name)
);
CREATE INDEX groupname_order_by_asc ON groups (name ASC);