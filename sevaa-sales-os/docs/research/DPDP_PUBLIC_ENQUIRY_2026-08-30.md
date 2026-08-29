# DPDP Public-Enquiry Readiness — 2026-08-30

This is implementation research for the SEVAA pilot, not a legal opinion. Re-check official law and obtain professional advice when the business/data risk justifies it.

## Primary-source timing

Official Gazette notifications published by the Ministry of Electronics and Information Technology on 13 November 2025 phase in the Digital Personal Data Protection Act, 2023 and Digital Personal Data Protection Rules, 2025.

At the repository review date of 30 August 2026:

- the Act commencement notification says sections 3–5, section 6(1)–(8) and (10), sections 7–17 and other listed provisions come into force **18 months after 13 November 2025**, i.e. 13 May 2027
- the Rules say Rule 3 and Rules 5–16, 22 and 23 come into force **18 months after publication**, also 13 May 2027
- Rule 4 comes into force one year after publication, 13 November 2026
- other provisions listed in the notifications have earlier commencement dates; do not infer that the entire Act/Rules are dormant

Sources reviewed:

- Gazette notification G.S.R. 843(E), 13 November 2025 — commencement of provisions of the DPDP Act, 2023
- Gazette notification G.S.R. 846(E), 13 November 2025 — Digital Personal Data Protection Rules, 2025

## Future notice standard relevant to `/quote`

Rule 3 states that the Data Fiduciary's notice should be independently understandable, clear and plain, and include at minimum:

- an itemised description of personal data
- the specified purpose(s) and description of the goods/services/use enabled by processing
- a link or other means through which a Data Principal can withdraw consent, exercise rights and make a complaint

The Act's consent provisions are also scheduled into force on the 18-month timetable described above.

## Engineering decision

Do not wait for the effective date to implement a transparent boundary. The public quote flow now:

1. provides a standalone `/privacy` notice
2. states the categories of data entered and the specific sales-enquiry purposes
3. warns users not to submit sensitive credentials or unrelated sensitive personal data
4. provides a privacy-request contact route, using `SEVAA_PUBLIC_CONTACT_EMAIL` when configured
5. requires a clear affirmative privacy-notice acknowledgement before the public enquiry API accepts a lead
6. preserves the existing founder approval gates; form submission does not authorize a contract, payment or autonomous outbound message

This is an early-readiness control, not a claim that the product has been certified legally compliant.

## Before broad public promotion

- configure `SEVAA_PUBLIC_CONTACT_EMAIL` to a monitored company mailbox
- have the company's legal/CA/privacy adviser verify the public notice, retention approach, GST/invoicing flow and any sector-specific obligations
- define and implement an evidence-based retention/deletion schedule once actual customer/data lifecycle is known
- document processors/sub-processors actually used in production hosting and messaging/payment integrations
- re-check the DPDP commencement schedule and any subsequent amendments/guidance before 13 May 2027

## Data minimisation rule

The quote form should remain limited to information needed to evaluate and follow up a project enquiry. Do not add government identifiers, payment credentials, medical data or unrelated profiling fields merely because the database can store them.
