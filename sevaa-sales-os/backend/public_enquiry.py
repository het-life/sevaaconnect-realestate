from __future__ import annotations

from fastapi import Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, model_validator

from backend.phase2 import ActorContext, LeadCreateV2, app, create_lead_v2


class PublicEnquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    company: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=120)
    requirement: str = Field(min_length=3, max_length=1000)
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    timeline_days: int | None = Field(default=None, ge=0, le=3650)
    website: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def require_contact(self):
        if not (self.phone and self.phone.strip()) and not (self.email and self.email.strip()):
            raise ValueError("phone or email is required")
        return self


@app.get("/quote", response_class=HTMLResponse)
def public_quote_page():
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Request a SEVAA project quote</title>
<style>
body{margin:0;background:#07100e;color:#eef7f3;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{max-width:760px;margin:0 auto;padding:42px 18px}.card{background:#101b18;border:1px solid #294139;border-radius:20px;padding:24px}h1{font-size:28px;margin:0 0 8px}.sub{color:#9ab0a8;line-height:1.5;margin:0 0 22px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.full{grid-column:1/-1}label{display:block;color:#9ab0a8;font-size:12px;margin:0 0 5px}input,textarea{width:100%;box-sizing:border-box;background:#09130f;color:#eef7f3;border:1px solid #2a463c;border-radius:10px;padding:11px;font:inherit}textarea{min-height:110px;resize:vertical}button{margin-top:18px;background:#9df5c9;color:#062015;border:0;border-radius:10px;padding:12px 17px;font-weight:760;cursor:pointer}.note{font-size:11px;color:#7f968e;margin-top:13px}.status{min-height:20px;margin-top:12px;color:#9df5c9}.trap{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}@media(max-width:650px){.grid{grid-template-columns:1fr}.full{grid-column:auto}}
</style>
</head>
<body><main class="wrap"><section class="card"><h1>Request a project quote</h1><p class="sub">Tell us what you need. Your enquiry enters the SEVAA review pipeline; pricing and commitments are reviewed before anything is approved.</p>
<form id="quoteForm"><div class="grid">
<div><label>Name *</label><input name="name" required maxlength="120"></div>
<div><label>Company</label><input name="company" maxlength="120"></div>
<div><label>Phone</label><input name="phone" maxlength="40" inputmode="tel"></div>
<div><label>Email</label><input name="email" maxlength="160" type="email"></div>
<div><label>City</label><input name="city" maxlength="120"></div>
<div><label>Timeline (days)</label><input name="timeline_days" min="0" max="3650" type="number"></div>
<div><label>Budget from (₹)</label><input name="budget_min" min="0" type="number"></div>
<div><label>Budget to (₹)</label><input name="budget_max" min="0" type="number"></div>
<div class="full"><label>Project requirement *</label><textarea name="requirement" required maxlength="1000" placeholder="Example: 20ft modular sales office, interiors required, delivery target 45 days"></textarea></div>
<div class="trap" aria-hidden="true"><label>Website</label><input name="website" tabindex="-1" autocomplete="off"></div>
</div><button type="submit">Send enquiry</button><div class="status" id="status"></div><div class="note">Submitting this form does not create a contract, payment obligation, or automatic external message.</div></form>
</section></main>
<script>
const form=document.getElementById('quoteForm'),statusEl=document.getElementById('status');
form.addEventListener('submit',async e=>{e.preventDefault();statusEl.textContent='Sending…';const data=Object.fromEntries(new FormData(form).entries());for(const key of ['budget_min','budget_max','timeline_days'])data[key]=data[key]?Number(data[key]):null;try{const r=await fetch('/api/v2/public/enquiries',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':'quote-'+crypto.randomUUID()},body:JSON.stringify(data)});const body=await r.json().catch(()=>({}));if(!r.ok)throw new Error(typeof body.detail==='string'?body.detail:'Please check the form and try again.');statusEl.textContent='Enquiry received. We will review it before any proposal is issued.';form.reset()}catch(err){statusEl.textContent=err.message||'Unable to send enquiry.'}});
</script></body></html>"""
    )


@app.post("/api/v2/public/enquiries", status_code=202)
def create_public_enquiry(
    payload: PublicEnquiryCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    # Honeypot submissions are acknowledged but discarded so automated spam does
    # not learn that it triggered a filter.
    if payload.website and payload.website.strip():
        return {"accepted": True}

    lead_payload = LeadCreateV2(
        name=payload.name,
        company=payload.company,
        phone=payload.phone,
        email=payload.email,
        city=payload.city,
        requirement=payload.requirement,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        timeline_days=payload.timeline_days,
        known_buyer=False,
        site_ready=False,
        source="public-quote",
        allow_duplicate=False,
    )
    actor = ActorContext(actor_id="public-quote", role="automation", auth_mode="local")
    try:
        result = create_lead_v2(lead_payload, idempotency_key=idempotency_key, actor=actor)
    except HTTPException as exc:
        detail = exc.detail
        if exc.status_code == 409 and isinstance(detail, dict) and detail.get("code") == "duplicate_lead":
            return {"accepted": True, "deduplicated": True}
        raise
    return {
        "accepted": True,
        "reference": f"L{result['id']}",
        "idempotent_replay": bool(result.get("idempotent_replay")),
    }


__all__ = ["PublicEnquiryCreate"]
