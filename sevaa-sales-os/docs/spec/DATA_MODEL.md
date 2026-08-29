# Data Model

Minimum entities:

## users
id
email
password_hash / auth_provider_id
name
created_at

## organizations
id
name
slug
country
timezone
created_at

## organization_members
organization_id
user_id
role

Roles:
OWNER
ADMIN
SALES
VIEWER

## business_profiles
organization_id
business_type
description
default_currency
brand_voice
contact_details_json

## product_catalog
id
organization_id
name
description
pricing_mode
base_price
price_min
price_max
pricing_formula_json
active

## leads
See PRODUCT_SPEC.md.

## lead_events
id
lead_id
event_type
channel
payload_json
created_at

## qualification_answers
id
lead_id
question_key
question_text
answer_text
normalized_value_json
created_at

## proposals
id
organization_id
lead_id
revision
status
currency
subtotal
tax
total
assumptions_json
scope_json
exclusions_json
body_markdown
created_at
approved_at
sent_at

## followups
id
organization_id
lead_id
due_at
status
channel
draft_message
sent_at
attempts

## audit_events
id
organization_id
actor_type
actor_id
action
object_type
object_id
metadata_json
created_at

## ai_usage
id
organization_id
operation
provider
model
input_units
output_units
estimated_cost
latency_ms
success
created_at

## subscriptions
organization_id
provider
provider_customer_id
provider_subscription_id
plan
status
trial_ends_at
current_period_end

## usage_counters
organization_id
period
metric
value
