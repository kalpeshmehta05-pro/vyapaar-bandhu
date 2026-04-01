"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";
import Link from "next/link";

/* ─── Animated Counter ─────────────────────────────────────────────── */
function Counter({ value, suffix = "" }: { value: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const end = value;
    const duration = 2000;
    const step = Math.ceil(end / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(start);
      }
    }, 16);
    return () => clearInterval(timer);
  }, [inView, value]);

  return (
    <span ref={ref} className="font-mono text-3xl font-bold text-white">
      {count.toLocaleString("en-IN")}
      {suffix}
    </span>
  );
}

/* ─── SECTION 1: HERO ──────────────────────────────────────────────── */
function HeroSection() {
  return (
    <section className="min-h-screen flex items-center relative overflow-hidden px-6 lg:px-16">
      {/* Background gradient orbs */}
      <div className="absolute top-[-200px] right-[-200px] w-[500px] h-[500px] bg-[#F5A623] rounded-full blur-[120px] opacity-10" />
      <div className="absolute bottom-[-100px] left-[-100px] w-[400px] h-[400px] bg-[#2563EB] rounded-full blur-[100px] opacity-10" />

      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Left: Text */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0 }}
            className="inline-block px-4 py-1.5 rounded-full bg-[#F5A623]/10 border border-[#F5A623]/20 text-[#F5A623] text-sm font-medium"
          >
            GSTR-3B Automation Platform
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl lg:text-7xl font-extrabold leading-tight"
          >
            Aapka CA.
          </motion.h1>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-5xl lg:text-7xl font-extrabold leading-tight text-[#F5A623]"
          >
            WhatsApp pe.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-lg text-white/60 max-w-md"
          >
            Business owner sends invoice photo on WhatsApp. CA gets GSTR-3B
            ready in minutes.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex gap-4 items-center"
          >
            <a
              href="#waitlist"
              className="px-6 py-3 bg-gradient-to-r from-[#F5A623] to-[#D4901E] text-black font-semibold rounded-lg hover:opacity-90 transition-opacity"
            >
              Start Free Trial
            </a>
            <a
              href="#how-it-works"
              className="px-6 py-3 border border-white/20 text-white rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z" />
              </svg>
              Watch Demo
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex items-center gap-3 text-sm text-white/40"
          >
            <div className="flex -space-x-2">
              {["#F5A623", "#22C55E", "#3B82F6", "#A855F7", "#EF4444"].map(
                (c, i) => (
                  <div
                    key={i}
                    className="w-7 h-7 rounded-full border-2 border-[#060B18]"
                    style={{ background: c }}
                  />
                )
              )}
            </div>
            500+ CAs on waitlist
          </motion.div>
        </div>

        {/* Right: Phone Mockup (CSS-only) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="hidden lg:flex justify-center"
        >
          <div className="relative w-[280px] h-[560px] bg-[#1a1a2e] rounded-[40px] border-2 border-[#F5A623]/20 shadow-2xl shadow-[#F5A623]/10 overflow-hidden">
            {/* Screen */}
            <div className="absolute inset-3 rounded-[32px] bg-[#0D1528] overflow-hidden">
              {/* WhatsApp header */}
              <div className="bg-[#075E54] px-4 py-3 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/20" />
                <div>
                  <div className="text-white text-sm font-medium">VyapaarBandhu</div>
                  <div className="text-white/60 text-xs">online</div>
                </div>
              </div>
              {/* Chat messages */}
              <div className="p-3 space-y-3 text-xs">
                <div className="bg-[#DCF8C6] text-black p-2.5 rounded-lg rounded-tr-none max-w-[75%] ml-auto">
                  invoice_hotel_march.jpg
                </div>
                <div className="bg-white/10 text-white p-2.5 rounded-lg rounded-tl-none max-w-[80%]">
                  Processing your invoice...
                </div>
                <div className="bg-white/10 text-white p-2.5 rounded-lg rounded-tl-none max-w-[80%] space-y-1">
                  <div className="text-green-400">Done!</div>
                  <div className="text-white/70">GSTIN: 27AAPFU...</div>
                  <div className="text-white/70">ITC: ₹18,400 confirmed</div>
                </div>
                <div className="bg-white/5 text-[#F5A623] p-2 rounded-lg text-center text-[11px]">
                  GSTR-3B ready for filing
                </div>
              </div>
            </div>
            {/* Notch */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-6 bg-[#1a1a2e] rounded-b-2xl" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

/* ─── SECTION 2: LIVE STATS ────────────────────────────────────────── */
function StatsBar() {
  return (
    <section className="border-t border-[#F5A623]/20 bg-[#0D1528] py-10">
      <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center px-6">
        {[
          { label: "Invoices Processed", value: 10247, suffix: "+" },
          { label: "CAs on Waitlist", value: 512, suffix: "+" },
          { label: "RCM Categories", value: 5, suffix: "" },
          { label: "Uptime", value: 99, suffix: ".9%" },
        ].map((s) => (
          <div key={s.label}>
            <Counter value={s.value} suffix={s.suffix} />
            <div className="text-white/40 text-sm mt-1">{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ─── SECTION 3: HOW IT WORKS ──────────────────────────────────────── */
function HowItWorks() {
  const steps = [
    {
      icon: "📱",
      title: "Business owner sends invoice",
      desc: "Any photo format -- JPG, PDF, screenshot. Hindi or English. Zero app download needed.",
    },
    {
      icon: "🔍",
      title: "VyapaarBandhu reads & classifies",
      desc: "OCR extracts GSTIN, amounts, HSN codes. RCM auto-detected. Confidence scored per field.",
    },
    {
      icon: "📄",
      title: "CA gets GSTR-3B ready",
      desc: "Exact GSTN portal JSON format. PDF report generated. Zero manual entry.",
    },
  ];

  return (
    <section id="how-it-works" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-16">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2 }}
              className="relative bg-[#0D1528] border border-white/5 rounded-xl p-8 text-center"
            >
              <div className="text-4xl mb-4">{step.icon}</div>
              <h3 className="font-semibold text-lg mb-3">{step.title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">
                {step.desc}
              </p>
              {i < 2 && (
                <div className="hidden md:block absolute top-1/2 -right-4 w-8 text-white/20 text-2xl">
                  &rarr;
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── SECTION 4: TRUST & COMPLIANCE ────────────────────────────────── */
function TrustSection() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-[#0D1528] border-2 border-[#F5A623]/20 rounded-2xl p-10"
        >
          <h2 className="text-2xl font-bold text-center mb-10">
            Built for Compliance. Built for Trust.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            <div>
              <h3 className="text-[#F5A623] font-semibold mb-4">
                GST Compliance
              </h3>
              <ul className="space-y-3 text-sm">
                {[
                  "DPDP Act 2023 -- Data protection compliant",
                  "RCM Section 9(4) CGST Act -- 5 categories covered",
                  "IGST Act Section 5(3) -- Import of services",
                  "Notification 13/2017-CT(R) -- Full RCM mapping",
                  "GSTIN Modulo-36 checksum -- Every GSTIN validated",
                  "Zero AI in tax logic -- 100% deterministic rules",
                  "Decimal math -- No floating point in tax calculations",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="text-[#F5A623] mt-0.5">&#10003;</span>
                    <span className="text-white/70">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-[#F5A623] font-semibold mb-4">Security</h3>
              <ul className="space-y-3 text-sm">
                {[
                  "RS256 JWT -- Bank-grade authentication",
                  "httpOnly cookies -- XSS attack protected",
                  "Row-Level Security -- CA data isolation",
                  "SHA-256 audit chain -- Legally defensible logs",
                  "SELECT FOR UPDATE -- Race-condition proof",
                  "Rate limiting -- Brute force protected",
                  "Security headers -- HSTS, CSP, X-Frame-Options",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">&#128274;</span>
                    <span className="text-white/70">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="text-center text-white/40 text-sm mt-8">
            Built for Indian CAs. Compliant with Indian law.
          </p>
        </motion.div>
      </div>
    </section>
  );
}

/* ─── SECTION 5: FEATURE BENTO ─────────────────────────────────────── */
function FeatureBento() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 auto-rows-fr">
          {/* Large card: WhatsApp State Machine */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="md:col-span-2 md:row-span-2 bg-[#0D1528] border border-white/5 rounded-xl p-8"
          >
            <h3 className="font-semibold text-lg mb-6">
              WhatsApp State Machine
            </h3>
            <div className="flex flex-wrap gap-3">
              {[
                { state: "IDLE", color: "bg-gray-500" },
                { state: "CONSENT", color: "bg-yellow-500" },
                { state: "AWAITING_IMAGE", color: "bg-blue-500" },
                { state: "PROCESSING", color: "bg-purple-500" },
                { state: "REVIEW", color: "bg-orange-500" },
                { state: "COMPLETED", color: "bg-green-500" },
              ].map((s, i) => (
                <motion.div
                  key={s.state}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.15 }}
                  className={`px-4 py-2 rounded-full text-xs font-mono text-white ${s.color}/20 border border-white/10`}
                >
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${s.color} mr-2`}
                  />
                  {s.state}
                </motion.div>
              ))}
            </div>
            <p className="text-white/40 text-sm mt-6">
              7-state conversation flow with DPDP consent gate, bilingual
              support, and idempotent message handling.
            </p>
          </motion.div>

          {/* Bilingual */}
          <div className="bg-[#0D1528] border border-white/5 rounded-xl p-6">
            <h3 className="font-semibold mb-3">Bilingual Support</h3>
            <div className="space-y-2 text-sm text-white/60">
              <p>&#127470;&#127475; Hindi + English</p>
              <p className="text-white/40 text-xs italic">
                &ldquo;Aapki invoice process ho gayi hai&rdquo;
              </p>
            </div>
          </div>

          {/* OCR Confidence */}
          <div className="bg-[#0D1528] border border-white/5 rounded-xl p-6">
            <h3 className="font-semibold mb-3">OCR Confidence</h3>
            <div className="space-y-2 text-xs">
              {[
                { field: "GSTIN", pct: 97 },
                { field: "Amount", pct: 94 },
                { field: "Date", pct: 88 },
                { field: "HSN", pct: 81 },
              ].map((f) => (
                <div key={f.field} className="flex items-center gap-2">
                  <span className="text-white/50 w-14">{f.field}</span>
                  <div className="flex-1 bg-white/5 rounded-full h-2">
                    <div
                      className="bg-[#F5A623] h-2 rounded-full"
                      style={{ width: `${f.pct}%` }}
                    />
                  </div>
                  <span className="text-white/40 w-8">{f.pct}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* RCM */}
          <div className="bg-[#0D1528] border border-white/5 rounded-xl p-6">
            <h3 className="font-semibold mb-3">RCM Detection</h3>
            <div className="flex flex-wrap gap-2">
              {["GTA", "Legal", "Security", "Import", "Unregistered"].map(
                (cat) => (
                  <span
                    key={cat}
                    className="px-2.5 py-1 rounded-full text-xs bg-purple-500/10 text-purple-300 border border-purple-500/20"
                  >
                    {cat}
                  </span>
                )
              )}
            </div>
          </div>

          {/* GSTR-3B Export */}
          <div className="md:col-span-2 bg-[#0D1528] border border-white/5 rounded-xl p-6">
            <h3 className="font-semibold mb-3">GSTR-3B Export</h3>
            <pre className="text-xs text-white/50 bg-black/30 rounded-lg p-4 overflow-x-auto">
              <code>{`{
  "gstin": "27AAPFU0939F1ZV",
  "ret_period": "032026",
  "itc_elg": {
    "itc_avl": [
      { "ty": "ISUP", "iamt": "18400.00", "camt": "0.00" }
    ]
  }
}`}</code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── SECTION 6: PRICING ───────────────────────────────────────────── */
function PricingSection() {
  const plans = [
    {
      name: "Starter",
      price: "0",
      period: "Free forever",
      features: [
        "Up to 5 clients",
        "50 invoices/month",
        "WhatsApp bot",
        "Basic dashboard",
        "Community support",
      ],
      cta: "Start Free",
      featured: false,
      border: "border-white/10",
    },
    {
      name: "Professional",
      price: "499",
      period: "/month",
      badge: "Most Popular",
      features: [
        "Up to 25 clients",
        "500 invoices/month",
        "GSTR-3B JSON export",
        "PDF reports",
        "Priority WhatsApp support",
        "Audit trail export",
      ],
      cta: "Start 14-Day Free Trial",
      featured: true,
      border: "border-[#F5A623]/40",
    },
    {
      name: "CA Firm",
      price: "999",
      period: "/month",
      features: [
        "Unlimited clients",
        "Unlimited invoices",
        "3 team members",
        "Custom onboarding",
        "Dedicated CA success manager",
        "SLA guarantee",
      ],
      cta: "Contact Sales",
      featured: false,
      border: "border-purple-500/20",
    },
  ];

  return (
    <section id="pricing" className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4">Pricing</h2>
        <p className="text-white/40 text-center mb-12">
          Save 20% with annual billing
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className={`relative bg-[#0D1528] border ${plan.border} rounded-xl p-8 ${
                plan.featured ? "shadow-lg shadow-[#F5A623]/10" : ""
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-[#F5A623] text-black text-xs font-bold rounded-full">
                  {plan.badge}
                </div>
              )}
              <h3 className="font-semibold text-lg mb-2">{plan.name}</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold">
                  &#8377;{plan.price}
                </span>
                <span className="text-white/40 text-sm">{plan.period}</span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2 text-sm text-white/60"
                  >
                    <span className="text-green-400">&#10003;</span> {f}
                  </li>
                ))}
              </ul>
              <a
                href="#waitlist"
                className={`block text-center py-3 rounded-lg font-semibold transition-opacity hover:opacity-90 ${
                  plan.featured
                    ? "bg-gradient-to-r from-[#F5A623] to-[#D4901E] text-black"
                    : "border border-white/20 text-white hover:bg-white/5"
                }`}
              >
                {plan.cta}
              </a>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── SECTION 7: WAITLIST ──────────────────────────────────────────── */
function WaitlistSection() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    city: "",
    role: "ca",
  });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name || !form.email || !form.phone) {
      setErrorMsg("Please fill in all required fields");
      setStatus("error");
      return;
    }

    setStatus("loading");

    try {
      // Submit to API or Supabase
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
      const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

      if (supabaseUrl && supabaseKey) {
        const res = await fetch(`${supabaseUrl}/rest/v1/waitlist`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            apikey: supabaseKey,
            Authorization: `Bearer ${supabaseKey}`,
          },
          body: JSON.stringify(form),
        });
        if (!res.ok) throw new Error("Failed to submit");
      }

      setStatus("success");
    } catch {
      setErrorMsg("Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <section id="waitlist" className="py-24 px-6">
        <div className="max-w-md mx-auto text-center">
          <div className="text-6xl mb-4">&#127881;</div>
          <h2 className="text-2xl font-bold mb-4">
            You&apos;re on the list!
          </h2>
          <p className="text-white/50">
            We&apos;ll WhatsApp you when we launch in your city.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section id="waitlist" className="py-24 px-6">
      <div className="max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-center mb-2">
          Join 500+ CAs getting early access.
        </h2>
        <p className="text-white/40 text-center mb-8">
          Free for first 100 CAs. No credit card needed.
        </p>

        {status === "error" && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Your Name"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-4 py-3 bg-[#0D1528] border border-white/10 rounded-lg text-white placeholder:text-white/30 focus:outline-none focus:border-[#F5A623]/50 transition-colors"
          />
          <input
            type="email"
            placeholder="Email address"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full px-4 py-3 bg-[#0D1528] border border-white/10 rounded-lg text-white placeholder:text-white/30 focus:outline-none focus:border-[#F5A623]/50 transition-colors"
          />
          <input
            type="tel"
            placeholder="+91 98765 43210"
            required
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="w-full px-4 py-3 bg-[#0D1528] border border-white/10 rounded-lg text-white placeholder:text-white/30 focus:outline-none focus:border-[#F5A623]/50 transition-colors"
          />
          <input
            type="text"
            placeholder="City (Ahmedabad, Surat, Mumbai...)"
            value={form.city}
            onChange={(e) => setForm({ ...form, city: e.target.value })}
            className="w-full px-4 py-3 bg-[#0D1528] border border-white/10 rounded-lg text-white placeholder:text-white/30 focus:outline-none focus:border-[#F5A623]/50 transition-colors"
          />
          <div className="flex gap-6 text-sm text-white/60">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="role"
                value="ca"
                checked={form.role === "ca"}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="accent-[#F5A623]"
              />
              CA
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="role"
                value="business_owner"
                checked={form.role === "business_owner"}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="accent-[#F5A623]"
              />
              Business Owner
            </label>
          </div>
          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full py-3 bg-gradient-to-r from-[#F5A623] to-[#D4901E] text-black font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {status === "loading" ? "Submitting..." : "Join the Waitlist \u2192"}
          </button>
        </form>
      </div>
    </section>
  );
}

/* ─── FOOTER ───────────────────────────────────────────────────────── */
function Footer() {
  return (
    <footer className="border-t border-white/5 py-12 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-lg mb-2">
              <span className="text-[#F5A623]">Vyapaar</span>Bandhu
            </h3>
            <p className="text-white/40 text-sm">
              AI-powered GST compliance for Indian SMEs
            </p>
          </div>
          <div className="flex gap-8 text-sm text-white/50">
            <div className="space-y-2">
              <a href="#how-it-works" className="block hover:text-white transition-colors">
                Features
              </a>
              <a href="#pricing" className="block hover:text-white transition-colors">
                Pricing
              </a>
            </div>
            <div className="space-y-2">
              <a href="#waitlist" className="block hover:text-white transition-colors">
                Contact
              </a>
              <Link href="/login" className="block hover:text-white transition-colors">
                CA Login
              </Link>
            </div>
          </div>
          <div className="text-sm text-white/40 md:text-right">
            Made in India for Indian CAs
          </div>
        </div>
        <div className="text-center text-xs text-white/30 border-t border-white/5 pt-6">
          &copy; 2026 VyapaarBandhu &middot; Privacy Policy &middot; DPDP Act
          2023 Compliant
        </div>
      </div>
    </footer>
  );
}

/* ─── MAIN PAGE ────────────────────────────────────────────────────── */
export default function MarketingPage() {
  return (
    <main className="bg-[#060B18] text-white min-h-screen font-[family-name:var(--font-outfit)]">
      <HeroSection />
      <StatsBar />
      <HowItWorks />
      <TrustSection />
      <FeatureBento />
      <PricingSection />
      <WaitlistSection />
      <Footer />
    </main>
  );
}
