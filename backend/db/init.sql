-- VyapaarBandhu — PostgreSQL Initialization Script
-- Creates the vyapaar schema and audit log protection rules.
-- Run by Docker on first container start.

CREATE SCHEMA IF NOT EXISTS vyapaar;

-- Audit log protection: prevent UPDATE and DELETE at database level.
-- These rules are applied after Alembic creates the table.
-- DO NOT REMOVE. The audit log must be append-only forever.

-- NOTE: Rules are created by Alembic migration after table creation.
-- This file only ensures the schema exists.
