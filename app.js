const BUY_URL = "";

const ids = ["price","rent","down","interest","term","costs"];
const el = id => document.getElementById(id);
const money = n => Number.isFinite(n) ? new Intl.NumberFormat("en-IN", { style:"currency", currency:"INR", maximumFractionDigits:0 }).format(n) : "—";
const pct = n => Number.isFinite(n) ? `${n.toFixed(2)}%` : "—";

function monthlyPayment(principal, annualRate, years){
  if (principal <= 0) return 0;
  const n = years * 12;
  const r = annualRate / 100 / 12;
  if (r === 0) return principal / n;
  return principal * r * Math.pow(1+r,n) / (Math.pow(1+r,n)-1);
}

function scoreDeal({cashflow,grossYield,capRate,coc,ltv}){
  let score = 50;
  score += Math.max(-20, Math.min(20, cashflow / 2500));
  score += Math.max(-10, Math.min(10, (grossYield - 4) * 2));
  score += Math.max(-10, Math.min(10, (capRate - 3) * 2));
  score += Math.max(-8, Math.min(8, coc / 2));
  if (ltv > 80) score -= 8; else if (ltv < 65) score += 4;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function calculate(){
  const price = +el("price").value || 0;
  const rent = +el("rent").value || 0;
  const down = +el("down").value || 0;
  const interest = +el("interest").value || 0;
  const term = +el("term").value || 1;
  const costs = +el("costs").value || 0;
  const loan = Math.max(0, price-down);
  const emi = monthlyPayment(loan, interest, term);
  const monthlyNOI = rent-costs;
  const cashflow = monthlyNOI-emi;
  const grossYield = price ? rent*12/price*100 : 0;
  const capRate = price ? monthlyNOI*12/price*100 : 0;
  const coc = down ? cashflow*12/down*100 : 0;
  const ltv = price ? loan/price*100 : 0;
  const score = scoreDeal({cashflow,grossYield,capRate,coc,ltv});

  el("emi").textContent = money(emi);
  el("cashflow").textContent = money(cashflow);
  el("yield").textContent = pct(grossYield);
  el("caprate").textContent = pct(capRate);
  el("coc").textContent = pct(coc);
  el("score").textContent = `${score}/100`;
}

ids.forEach(id => el(id).addEventListener("input", calculate));
el("resetButton").addEventListener("click", () => { el("dealForm").reset(); calculate(); });

const buyButton = el("buyButton");
if (BUY_URL){ buyButton.href = BUY_URL; el("checkoutNote").textContent = "Secure checkout • instant digital delivery"; }
else { buyButton.addEventListener("click", e => e.preventDefault()); }
calculate();
