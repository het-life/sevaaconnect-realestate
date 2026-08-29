# FOUNDER REQUIREMENTS / CHECKUP

This file contains **no passwords, API secrets, private keys, OTPs, bank credentials, UPI PINs or recovery codes**. It records only what the automation needs from the founder and whether that dependency is resolved.

## Immediate action needed

### public_host_authorization — NEEDED
Authorize/create the public pilot host and any resulting recurring charge. Current selected shortest path is Railway; the deployment procedure and rollback are in `docs/spec/DEPLOYMENT.md`.

At the 2026-08-30 research point, Railway published a $1/month Free plan after the trial and a $5-minimum Hobby plan. Re-check provider pricing before committing spend because pricing is external and can change.

Do not put hosting credentials, API tokens, server passwords or private keys in Git.

### production_app_secrets — NEEDED WITH HOST
Create different high-entropy values for `SEVAA_FOUNDER_TOKEN` and `SEVAA_AUTOMATION_TOKEN` directly in the host secret store. Keep `SEVAA_ALLOW_LEGACY_V1=0`.

The values themselves must never be recorded here.

### real_traffic_source — NEEDED AFTER DEPLOYMENT VERIFICATION
Choose one first lawful source to route into `/quote`: an existing site/profile, WhatsApp Business profile, warm outreach, a referral, or a paid campaign only after budget approval. No unsolicited bulk messaging.

### first_buyer — NEEDED AFTER DEPLOYMENT
Route at least one genuinely interested external buyer/enquiry through the system so simulated assumptions can begin being replaced with observed data.

## Needed only when the workflow reaches the condition

### buyer_contact_email — NEEDED BEFORE BROADER PUBLIC PROMOTION
Choose the public sales/contact identity shown to buyers. It is not required to run the technical deployment or a controlled first-pilot enquiry.

### razorpay_credentials — NEEDED ONLY FOR REAL PAYMENT COLLECTION
Configure `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` only in the production host secret store when a founder-reviewed approved proposal actually needs a payment link. Never paste values into repository docs or prompts.

### tax_configuration_ca_review — NEEDED BEFORE MATERIAL SCALE / FINAL TAX AUTOMATION
Have the company CA confirm GST classification/rate, input-tax-credit treatment, invoicing requirements and actual company-tax regime. Do not send tax portal passwords or DSC credentials.

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
- Founder and automation authorization model — implemented and tested.

## Agent rule

When blocked by a login, connector, credential, legal/business choice, device access, domain, external account, or consequential spend, update this register first and continue every independent task before asking the founder.
