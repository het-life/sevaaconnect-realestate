# FOUNDER REQUIREMENTS / CHECKUP

This file contains **no passwords, API secrets, private keys, OTPs, bank credentials, UPI PINs or recovery codes**. It records only what the automation needs from the founder and whether that dependency is resolved.

## Immediate action needed

### public_host_authorization — NEEDED
Authorize/connect a Railway account/project so the validated pilot can be deployed. The deployment procedure and rollback are in `docs/spec/DEPLOYMENT.md`.

Railway documentation re-checked on 2026-08-30:
- a new user can start the free Trial **without a credit card**
- the Trial provides a one-time $5 credit for up to 30 days
- after the Trial, Railway documents a Free plan with $1/month of free credit
- Trial and Free both list up to 0.5 GB volume storage
- Hobby remains a paid $5 minimum-usage tier with $5 included usage

Therefore the immediate gate is account/login authorization, not a required paid subscription. Use the no-card Trial/Free path first. Do not accept Hobby, another paid plan, or excess-use charges unless the free path proves insufficient and the founder explicitly approves the spend.

Provider pricing and eligibility can change, so re-check the account billing screen before any paid upgrade.

Do not put hosting credentials, API tokens, server passwords or private keys in Git.

### production_app_secrets — NEEDED WITH HOST
Create different high-entropy values for `SEVAA_FOUNDER_TOKEN` and `SEVAA_AUTOMATION_TOKEN` directly in the host secret store. Keep `SEVAA_ALLOW_LEGACY_V1=0`.

The values themselves must never be recorded here.

### real_traffic_source — NEEDED AFTER DEPLOYMENT VERIFICATION
Choose one first lawful source to route into `/quote`: an existing site/profile, WhatsApp Business profile, warm outreach, a referral, or a paid campaign only after budget approval. No unsolicited bulk messaging.

### first_buyer — NEEDED AFTER DEPLOYMENT
Route at least one genuinely interested external buyer/enquiry through the system so simulated assumptions can begin being replaced with observed data.

## Needed before broader public promotion

### public_privacy_contact — NEEDED
Choose a monitored company mailbox for privacy/access/correction/deletion/withdrawal requests and configure it as `SEVAA_PUBLIC_CONTACT_EMAIL` in the host environment. The value is public contact information, not a secret, but it should still be managed through deployment configuration rather than hardcoded into application code.

The controlled first-pilot link can technically operate with the documented fallback contact channel, but broad promotion should wait until this mailbox is configured and `/privacy` has been reviewed against the actual production processors/workflow.

## Needed only when the workflow reaches the condition

### razorpay_credentials — NEEDED ONLY FOR REAL PAYMENT COLLECTION
Configure `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` only in the production host secret store when a founder-reviewed approved proposal actually needs a payment link. Never paste values into repository docs or prompts.

### tax_configuration_ca_review — NEEDED BEFORE MATERIAL SCALE / FINAL TAX AUTOMATION
Have the company CA confirm GST classification/rate, input-tax-credit treatment, invoicing requirements and actual company-tax regime. Do not send tax portal passwords or DSC credentials.

### privacy_legal_review — NEEDED BEFORE MATERIAL SCALE / 2027 CORE COMMENCEMENT
Have a qualified adviser re-check the deployed privacy notice, retention approach, actual processors and the DPDP commencement/guidance before material scale and before the 13 May 2027 core commencement milestone recorded in `docs/research/DPDP_PUBLIC_ENQUIRY_2026-08-30.md`.

### real_acquisition_budget — NEEDED LATER
After the first paid pilot, approve a maximum monthly acquisition budget inside the project capital envelope. Until then paid acquisition remains paper-only unless explicitly authorized for a controlled experiment.

## Not required for the first pilot

### custom_domain — OPTIONAL
Railway can provide the initial public HTTPS origin. Add a custom domain/subdomain once branding or trust justifies it; lack of a custom domain must not block the first controlled real-world validation.

### postgres — DEFERRED UNTIL MEASURED SCALE TRIGGER
The validated pilot is intentionally single-instance SQLite with a persistent volume and restore tooling. PostgreSQL becomes required only if horizontal replicas, lock contention, shared database consumers, or stronger database-service recovery requirements are measured.

## Already available

- GitHub connector — connected.
- Validated Docker deployment artifact — available.
- Public `/quote` acquisition path — implemented and tested.
- Public `/privacy` notice + affirmative acknowledgement + versioned audit evidence — merged to `main` and tested.
- Founder and automation authorization model — implemented and tested.

## Agent rule

When blocked by a login, connector, credential, legal/business choice, device access, domain, external account, or consequential spend, update this register first and continue every independent task before asking the founder.
