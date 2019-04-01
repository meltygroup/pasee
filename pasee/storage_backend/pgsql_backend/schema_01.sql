CREATE DATABASE pasee;

CREATE TABLE "groups" ("id" serial NOT NULL PRIMARY KEY, "name" text NOT NULL UNIQUE);
CREATE TABLE "users" ("id" serial NOT NULL PRIMARY KEY, "username" text NOT NULL UNIQUE, "is_banned" boolean DEFAULT FALSE);
CREATE TABLE "user_in_group" ("id" serial NOT NULL PRIMARY KEY, "user_id" integer NOT NULL, "group_id" integer NOT NULL);
CREATE INDEX "groups_name_46b2c599_like" ON "groups" ("name" text_pattern_ops);
CREATE INDEX "users_username_e8658fc8_like" ON "users" ("username" text_pattern_ops);
ALTER TABLE "user_in_group" ADD CONSTRAINT "user_in_group_user_id_8b54342e_fk_users_id" FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "user_in_group" ADD CONSTRAINT "user_in_group_group_id_2691306a_fk_groups_id" FOREIGN KEY ("group_id") REFERENCES "groups" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "user_in_group" ADD CONSTRAINT "user_in_group_user_id_group_id_1e50f3dc_uniq" UNIQUE ("user_id", "group_id");
CREATE INDEX "user_in_group_user_id_8b54342e" ON "user_in_group" ("user_id");
CREATE INDEX "user_in_group_group_id_2691306a" ON "user_in_group" ("group_id");
