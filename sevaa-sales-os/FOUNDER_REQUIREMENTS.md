# FOUNDER REQUIREMENTS / CHECKUP

This file contains **no passwords, API secrets, private keys, OTPs, bank credentials, UPI PINs or recovery codes**. It records only what the automation needs from the founder and whether that dependency is resolved.

## Immediate action needed

### public_host_authorization — NEEDED
Authorize/create the public pilot host and any resulting recurring charge. Current selected shortest path is Railway; the deployment procedure and rollback are in `docs/spec/DEPLOYMENT.md`.

Railway pricing re-checked on 2026-08-30 from its official pricing page:
- new users can receive a 30-day trial with a one-time $5 credit
- the page labels Free as `$0/month` but also states `then $1 per month` after the trial; treat the exact post-trial Free charge as ambiguous until the account checkout/billing screen confirms it
- Free lists a 0.5 GB volume limit
- Hobby is $5 minimum monthly usage and includes $5 of monthly usage, with up to 5 GB volume storage

Provider pricing remains external and changeable. Verify the actual checkout/upgrade screen before accepting a charge. The pilot should start on the lowest tier that demonstrably provides the required public networking and persistent-volume behavior; do not upgrade merely to spend budget.

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
- Public `/privacy` notice + affirmative acknowledgement — implemented and tested on PR #6.
- Founder and automation authorization model — implemented and tested.

## Agent rule

When blocked by a login, connector, credential, legal/business choice, device access, domain, external account, or consequential spend, update this register first and continue every independent task before asking the founder.
