"use client";

import Link from "next/link";
import { ShoppingCart, Sparkles, Heart, ArrowRight, Star, Shield, Users } from "lucide-react";

function VitaRootsLogo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 56 56" xmlns="http://www.w3.org/2000/svg">
      <path d="M28 40 Q20 44 13 49" stroke="#3B2010" strokeWidth="1.4" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q24 46 21 52" stroke="#3B2010" strokeWidth="1.1" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q29 47 28 53" stroke="#3B2010" strokeWidth="0.9" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q33 45 36 51" stroke="#3B2010" strokeWidth="1.1" fill="none" strokeLinecap="round"/>
      <path d="M28 40 Q35 43 42 48" stroke="#3B2010" strokeWidth="1.4" fill="none" strokeLinecap="round"/>
      <path d="M28 40 L28 18" stroke="#3E6B4A" strokeWidth="2.2" fill="none" strokeLinecap="round"/>
      <path d="M28 30 Q20 24 14 20" stroke="#3E6B4A" strokeWidth="1.6" fill="none" strokeLinecap="round"/>
      <path d="M28 24 Q22 17 17 13" stroke="#3E6B4A" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
      <path d="M28 31 Q36 25 41 21" stroke="#3E6B4A" strokeWidth="1.6" fill="none" strokeLinecap="round"/>
      <path d="M28 24 Q34 17 39 13" stroke="#3E6B4A" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
      <ellipse cx="13" cy="19" rx="5" ry="3" fill="#5E8A68" transform="rotate(-35 13 19)"/>
      <ellipse cx="42" cy="20" rx="5" ry="3" fill="#5E8A68" transform="rotate(35 42 20)"/>
      <ellipse cx="28" cy="13" rx="6" ry="3.5" fill="#2E4A35"/>
      <circle cx="11" cy="17" r="2" fill="#C05A2B"/>
      <circle cx="43" cy="18" r="2" fill="#C05A2B"/>
      <circle cx="28" cy="9" r="2.5" fill="#D6854A"/>
    </svg>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen" style={{ background: "#FAF5ED" }}>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b" style={{ background: "rgba(250,245,237,0.92)", backdropFilter: "blur(12px)", borderColor: "rgba(201,169,110,0.18)" }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <VitaRootsLogo size={28} />
            <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", fontWeight: 700, color: "#1E1208" }}>
              Vita<span style={{ color: "#3E6B4A" }}>Roots</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="btn-ghost text-sm" style={{ color: "#3B2010" }}>
              Dashboard
            </Link>
            <Link
              href="/onboarding"
              className="text-sm font-medium px-5 py-2.5 rounded-full transition-all"
              style={{ background: "#3E6B4A", color: "#FAF5ED", fontFamily: "'Jost', sans-serif", letterSpacing: "0.06em" }}
              onMouseEnter={e => (e.currentTarget.style.background = "#2E4A35")}
              onMouseLeave={e => (e.currentTarget.style.background = "#3E6B4A")}
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
        <div
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-8"
          style={{ background: "rgba(214,133,74,0.12)", color: "#D6854A", fontFamily: "'Jost', sans-serif", letterSpacing: "0.1em", fontSize: "10px", textTransform: "uppercase" }}
        >
          <Sparkles className="w-3.5 h-3.5" />
          Intelligent Family Nutrition · Powered by Claude AI
        </div>

        <h1
          className="mb-6 leading-tight"
          style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "clamp(44px, 7vw, 72px)", fontWeight: 700, color: "#1E1208", letterSpacing: "-1px" }}
        >
          One plan.{" "}
          <em style={{ color: "#3E6B4A", fontStyle: "italic" }}>Every age.</em>
          <br />
          Every need.
        </h1>

        <p
          className="max-w-2xl mx-auto mb-10 leading-relaxed"
          style={{ fontSize: "17px", fontWeight: 300, color: "#7A3B1E", fontFamily: "'Jost', sans-serif" }}
        >
          VitaRoots is the AI-powered nutrition manager built for the whole family — from
          grandparents to grandchildren. Personalized meal plans, smart grocery lists, and
          holistic supplement guidance, unified in one intelligent platform.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 text-base font-medium px-8 py-4 rounded-full transition-all"
            style={{ background: "#3E6B4A", color: "#FAF5ED", fontFamily: "'Jost', sans-serif" }}
          >
            Start Your Family Plan
            <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 text-base font-medium px-8 py-4 rounded-full border transition-all"
            style={{ color: "#3B2010", borderColor: "rgba(201,169,110,0.4)", background: "transparent", fontFamily: "'Jost', sans-serif" }}
          >
            View Live Demo
          </Link>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-6 mt-10 text-sm" style={{ color: "#C9A96E", fontFamily: "'Jost', sans-serif", fontSize: "12px", letterSpacing: "0.05em" }}>
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            Informational only — not medical advice
          </div>
          <div className="flex items-center gap-1.5">
            <Star className="w-3.5 h-3.5" />
            Holistic &amp; evidence-informed
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5" />
            Built for multigenerational families
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-3 gap-8">

          {/* Meal Plans */}
          <div
            className="rounded-2xl p-8 transition-all duration-300 group"
            style={{ background: "#FDFAF4", border: "1px solid rgba(201,169,110,0.2)", boxShadow: "0 1px 4px rgba(30,18,8,0.05)" }}
          >
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 transition-colors"
              style={{ background: "rgba(62,107,74,0.1)" }}
            >
              <VitaRootsLogo size={28} />
            </div>
            <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", fontWeight: 600, color: "#1E1208", marginBottom: "10px" }}>
              Personalized Meal Plans
            </h3>
            <p style={{ color: "#7A3B1E", fontWeight: 300, lineHeight: 1.8, fontSize: "14px" }}>
              7-day meal plans crafted for your whole family. Each meal accounts for individual
              dietary needs, wellness philosophies (Ayurvedic, TCM, Western integrative), and
              flavor preferences — with per-member explanations.
            </p>
            <ul className="mt-5 space-y-2" style={{ fontSize: "13px", color: "#3B2010" }}>
              {["Per-member 'why it works' explanations", "Prep & cook time estimates", "Allergy & preference aware", "One-click meal swaps"].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <span style={{ color: "#D6854A", fontSize: "8px", marginTop: "5px", flexShrink: 0 }}>✦</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Grocery Lists */}
          <div
            className="rounded-2xl p-8 transition-all duration-300"
            style={{ background: "#FDFAF4", border: "2px solid rgba(214,133,74,0.25)", boxShadow: "0 1px 4px rgba(30,18,8,0.05)" }}
          >
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: "rgba(214,133,74,0.1)" }}
            >
              <ShoppingCart className="w-7 h-7" style={{ color: "#D6854A" }} />
            </div>
            <div
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold mb-4"
              style={{ background: "rgba(214,133,74,0.12)", color: "#D6854A", fontFamily: "'Jost', sans-serif", fontSize: "10px", letterSpacing: "0.1em" }}
            >
              <Star className="w-3 h-3" />
              Most Popular
            </div>
            <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", fontWeight: 600, color: "#1E1208", marginBottom: "10px" }}>
              Smart Grocery Lists
            </h3>
            <p style={{ color: "#7A3B1E", fontWeight: 300, lineHeight: 1.8, fontSize: "14px" }}>
              Auto-generated, categorized grocery lists with budget tracking. Flags organic and
              local items, consolidates ingredients across all meals, and offers money-saving tips.
            </p>
            <ul className="mt-5 space-y-2" style={{ fontSize: "13px", color: "#3B2010" }}>
              {["Budget progress tracker", "Organic & local item flags", "Category-sorted checklist", "Member-specific tagging"].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <span style={{ color: "#D6854A", fontSize: "8px", marginTop: "5px", flexShrink: 0 }}>✦</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Supplement Guidance */}
          <div
            className="rounded-2xl p-8 transition-all duration-300"
            style={{ background: "#FDFAF4", border: "1px solid rgba(201,169,110,0.2)", boxShadow: "0 1px 4px rgba(30,18,8,0.05)" }}
          >
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: "rgba(201,169,110,0.12)" }}
            >
              <Heart className="w-7 h-7" style={{ color: "#C9A96E" }} />
            </div>
            <h3 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", fontWeight: 600, color: "#1E1208", marginBottom: "10px" }}>
              Wellness Guidance
            </h3>
            <p style={{ color: "#7A3B1E", fontWeight: 300, lineHeight: 1.8, fontSize: "14px" }}>
              Personalized supplement suggestions aligned to each member's philosophy — Ayurvedic
              herbs, TCM tonics, or Western integrative nutraceuticals — with dosage and timing.
            </p>
            <ul className="mt-5 space-y-2" style={{ fontSize: "13px", color: "#3B2010" }}>
              {["Philosophy-aligned suggestions", "Dose range & timing", "Contraindication awareness", "Life-stage considerations"].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <span style={{ color: "#C9A96E", fontSize: "8px", marginTop: "5px", flexShrink: 0 }}>✦</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

        </div>
      </section>

      {/* How It Works */}
      <section className="py-20" style={{ background: "#FDFAF4", borderTop: "1px solid rgba(201,169,110,0.18)", borderBottom: "1px solid rgba(201,169,110,0.18)" }}>
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <div style={{ fontSize: "10px", letterSpacing: "0.3em", textTransform: "uppercase", color: "#D6854A", fontWeight: 600, fontFamily: "'Jost', sans-serif", marginBottom: "12px" }}>
              How It Works
            </div>
            <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "48px", fontWeight: 700, color: "#1E1208", lineHeight: 1.1 }}>
              Three steps to a healthier{" "}
              <em style={{ color: "#3E6B4A", fontStyle: "italic" }}>family table</em>
            </h2>
            <p className="mt-4 max-w-xl mx-auto" style={{ fontSize: "15px", fontWeight: 300, color: "#7A3B1E", lineHeight: 1.8 }}>
              VitaRoots makes intelligent nutrition simple — no conflicting advice, no one-size-fits-all plans.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                num: "1",
                title: "Tell us about your family",
                desc: "Each member gets their own profile — age, health conditions, dietary preferences, supplements, and goals. It takes minutes.",
                color: "rgba(62,107,74,0.1)",
                numColor: "#3E6B4A",
              },
              {
                num: "2",
                title: "Your plan is built intelligently",
                desc: "VitaRoots generates a unified family meal and supplement plan that works for everyone simultaneously — no more separate meals.",
                color: "rgba(214,133,74,0.1)",
                numColor: "#C05A2B",
              },
              {
                num: "3",
                title: "Your plan grows with you",
                desc: "VitaRoots refines week over week based on your family's feedback, health data, and seasonal changes.",
                color: "rgba(201,169,110,0.15)",
                numColor: "#7A3B1E",
              },
            ].map(({ num, title, desc, color, numColor }) => (
              <div
                key={num}
                className="rounded-2xl p-9 transition-all"
                style={{ background: "#FAF5ED", border: "1px solid rgba(201,169,110,0.18)" }}
              >
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center mb-6"
                  style={{ background: color, fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", fontWeight: 700, color: numColor }}
                >
                  {num}
                </div>
                <h4 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "22px", fontWeight: 600, color: "#1E1208", marginBottom: "10px" }}>
                  {title}
                </h4>
                <p style={{ fontSize: "13px", fontWeight: 300, color: "#7A3B1E", lineHeight: 1.8 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <div className="rounded-3xl px-8 py-16" style={{ background: "#1E1208" }}>
          <div style={{ fontSize: "10px", letterSpacing: "0.3em", textTransform: "uppercase", color: "#D6854A", fontWeight: 600, fontFamily: "'Jost', sans-serif", marginBottom: "16px" }}>
            Get Started Today
          </div>
          <h2 style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "clamp(36px, 5vw, 52px)", fontWeight: 700, color: "#FAF5ED", lineHeight: 1.1, marginBottom: "16px" }}>
            Your family&rsquo;s roots deserve{" "}
            <em style={{ color: "#5E8A68", fontStyle: "italic" }}>to thrive.</em>
          </h2>
          <p className="max-w-md mx-auto mb-10" style={{ fontSize: "15px", fontWeight: 300, color: "rgba(250,245,237,0.65)", lineHeight: 1.8 }}>
            Set up your family profile in under 5 minutes and get your first personalized meal plan instantly.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 font-medium px-8 py-4 rounded-full transition-all"
            style={{ background: "#3E6B4A", color: "#FAF5ED", fontSize: "14px", fontFamily: "'Jost', sans-serif", letterSpacing: "0.06em" }}
          >
            Start Your Family Plan
            <ArrowRight className="w-5 h-5" />
          </Link>
          <p className="mt-5" style={{ fontSize: "11px", color: "#C9A96E", fontFamily: "'Jost', sans-serif" }}>
            ✦ No account required · Suggestions are informational — always consult your healthcare provider.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid rgba(201,169,110,0.18)", background: "#1E1208" }}>
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <VitaRootsLogo size={22} />
              <span style={{ fontFamily: "'Cormorant Garamond', serif", fontSize: "20px", fontWeight: 700, color: "#FAF5ED" }}>
                Vita<span style={{ color: "#D6854A" }}>Roots</span>
              </span>
            </div>
            <p style={{ fontSize: "11px", color: "rgba(250,245,237,0.4)", marginTop: "4px", fontWeight: 300 }}>
              Where family health takes root.
            </p>
          </div>
          <p className="text-center text-xs" style={{ color: "rgba(250,245,237,0.35)", maxWidth: "420px", lineHeight: 1.6 }}>
            VitaRoots provides informational wellness guidance only, not medical advice.
            Always consult a licensed healthcare provider before making health decisions.
          </p>
        </div>
      </footer>

    </div>
  );
}
