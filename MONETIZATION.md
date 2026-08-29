# Monetization Plan — DealLens

## Objective
Reach the first legitimate paid customer with the least infrastructure and operating cost.

## Product
DealLens Pro: a single-file offline real-estate deal analyzer for brokers and property investors.

## Initial price
- Launch: ₹499 one-time for first 25 customers.
- Standard after validation: ₹999 one-time.
- Do **not** start with a subscription. First prove willingness to pay.

## Why this route
- Product is digital: near-zero marginal delivery cost.
- No database or server is required for the downloadable product.
- Customer data stays on-device.
- Lemon Squeezy supports digital product files, one-time pricing, license keys and checkout links.
- Alternative India-first rail: Razorpay Payment Pages. It is excellent for collecting payment, but automated digital fulfilment requires an additional webhook/delivery layer.

## Launch offer
“Screen a property deal in under 60 seconds. DealLens Pro calculates cash flow, cap rate, DSCR, break-even occupancy, cash-on-cash return and stress scenarios — without spreadsheets or uploading private deal data.”

## Buyer
1. Independent property brokers.
2. Small real-estate investors.
3. Real-estate sales teams who repeatedly compare rental/investment deals.

## Validation rule
Do not build a SaaS backend until one of these occurs:
- 10 paid one-time customers, or
- 3 customers independently request sync/team features, or
- ₹5,000 cumulative product revenue.

## Checkout boundary
Recommended: Lemon Squeezy for the first automated digital-download sale because it can host product files and issue license keys.

Required human/account action:
1. Create/activate a Lemon Squeezy store.
2. Complete identity/payout setup.
3. Create product “DealLens Pro”.
4. Price at ₹499 INR one-time.
5. Upload `DealLens-Pro-v1.html`.
6. Publish and paste the checkout URL into `BUY_URL` in `app.js`.

## Distribution experiments
Run cheap tests in this order:
1. Send demo URL to 10 known brokers/investors and ask only: “Would you pay ₹499 for the Pro version?” Record yes/no and objections.
2. Post a 20–30 second screen recording in local broker/real-estate communities where promotion is allowed.
3. Only after positive signal, test a small paid ad budget with a strict cap and explicit approval.

## Success metric
First completed paid order. Revenue is not considered achieved until the payment platform reports a successful real transaction.
