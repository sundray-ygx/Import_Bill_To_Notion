-- Migration 002: Add review-related fields to user_notion_configs table
-- Date: 2026-02-28
-- Description: Add monthly, quarterly, yearly review database and template IDs

-- Monthly review configuration
ALTER TABLE user_notion_configs ADD COLUMN notion_monthly_review_db VARCHAR(100);
ALTER TABLE user_notion_configs ADD COLUMN notion_monthly_template_id VARCHAR(100);

-- Quarterly review configuration
ALTER TABLE user_notion_configs ADD COLUMN notion_quarterly_review_db VARCHAR(100);
ALTER TABLE user_notion_configs ADD COLUMN notion_quarterly_template_id VARCHAR(100);

-- Yearly review configuration
ALTER TABLE user_notion_configs ADD COLUMN notion_yearly_review_db VARCHAR(100);
ALTER TABLE user_notion_configs ADD COLUMN notion_yearly_template_id VARCHAR(100);
