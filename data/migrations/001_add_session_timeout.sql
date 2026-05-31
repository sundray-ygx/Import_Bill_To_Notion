-- Migration 001: Add session_timeout_minutes column to users table
-- Date: 2026-02-28
-- Description: User model defines session_timeout_minutes but database table was missing this column

ALTER TABLE users ADD COLUMN session_timeout_minutes INTEGER NOT NULL DEFAULT 15;
