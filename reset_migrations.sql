-- Run this SQL to fix migration issues
-- This clears the migration history so we can start fresh

DELETE FROM django_migrations WHERE app = 'accounts';
DELETE FROM django_migrations WHERE app = 'admin';
DELETE FROM django_migrations WHERE app = 'auth';
DELETE FROM django_migrations WHERE app = 'contenttypes';
DELETE FROM django_migrations WHERE app = 'sessions';

-- Drop auth related tables
DROP TABLE IF EXISTS auth_user_groups;
DROP TABLE IF EXISTS auth_user_user_permissions;
DROP TABLE IF EXISTS auth_user;
DROP TABLE IF EXISTS auth_group_permissions;
DROP TABLE IF EXISTS auth_group;
DROP TABLE IF EXISTS auth_permission;
