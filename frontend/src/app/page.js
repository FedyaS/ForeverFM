'use client';

import Image from "next/image";
import Link from "next/link";
import styles from "./styles/page.module.css";
import "./styles/topics.css";

const topics = [
  {
    name: "Gaming",
    slug: "gaming",
    description: "Game dev, eSports, narrative design, and play culture.",
    bg: "",
    realColor: "#a930ff",
    image: "/categories/category-gaming.svg",
    filter: "invert(.6) sepia(1) contrast(15) hue-rotate(259deg)",
  },
  {
    name: "Technology",
    slug: "technology",
    description: "AI, software, gadgets, and how it all connects.",
    bg: "",
    realColor: "#6c6ef1",
    image: "/categories/category-tech.svg",
    filter: "invert(0.6) sepia(1) contrast(15) brightness(0.7) hue-rotate(180deg)",
  },
  {
    name: "Finance",
    slug: "finance",
    description: "Markets, money, investing, and economic ideas.",
    bg: "",
    realColor: "#7ecb00",
    image: "/categories/category-finance.svg",
    filter: "invert(0.6) sepia(1) contrast(15) brightness(3) hue-rotate(34deg)",
  },
  {
    name: "Health & Wellness",
    slug: "health",
    description: "Fitness, mental wellness, nutrition, and biohacking.",
    bg: "",
    realColor: "#ff008e",
    image: "/categories/category-health.svg",
    filter: "invert(0.6) sepia(1) contrast(15) brightness(3) hue-rotate(277deg)",
  },
  {
    name: "Real Estate",
    slug: "real-estate",
    description: "Housing, land, and future trends in living spaces.",
    bg: "",
    realColor: "#ffb300",
    image: "/categories/category-real-estate.svg",
    filter: "invert(0.6) sepia(1) contrast(12) brightness(3) hue-rotate(336deg)",
  },
];

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
      <h1 className={styles.title} style={{ color: '#74ff74' }}>ForeverFM</h1>
      <p className={styles.description}>
          Your brain learns by listening. ForeverFM is the 24/7 AI podcast station built to make you fluent in topics you didn’t even know you were curious about.
        </p>

        <p className={styles.subdescription}>
          Our AI-powered hosts simulate deep, fluent conversations across tech, finance, wellness, creativity, and more — so you can absorb new ideas passively, like you were born to do.
        </p>

        <div className={styles.ctas}>
          <Link href="/live" className={styles.primary}>Try it out</Link>
          <Link href="/about" className={styles.secondary}>Meet the Forever team</Link>
        </div>

        {/* Scrollable card section */}
        <div className="section">
          <h2 className="sectionTitle">Featured Topics</h2>
          <div className="scrollRowWrapper">
            <div className="scrollRow">
              {topics.map((topic) => (
                <div key={topic.slug} className="card" style={{color: topic.realColor, background: "linear-gradient(rgba(0, 0, 0, 0), rgba(255, 255, 255, 0.33))", filter: topic.filter}}>
                  <div className="thumbnail" style={{ background: topic.bg, filter: topic.filter}}>
                    {topic.image && (
                      <img
                        src={topic.image}
                        alt={topic.name}
                        className="thumbImage"
                      />
                    )}
                  </div>
                  <h3>{topic.name}</h3>
                  <p>{topic.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
          {/* Continuous Learning Section */}
<section>

<div className="section" style={{ textAlign: "left", maxWidth: "700px", margin: "3rem auto" }}>
  <h2 className="sectionTitle" style={{ textAlign: "left" }}>
    Continuous Learning, Powered by AI Conversations
  </h2>
  <p style={{ lineHeight: "1.6", marginTop: "1rem" }}>
    Real conversations. Real learning. Zero friction. Our AI hosts explore topics dynamically,
    letting you dive deep or stay casual—all based on your curiosity. Whether it&apos;s finance, tech,
    wellness, or gaming, you&apos;re just one click away from immersive learning.
  </p>
  <ul style={{ marginTop: "1rem", paddingLeft: "1.25rem" }}>
    <li>Listen 24/7 to evolving expert-like discussions</li>
    <li>Guide the conversation without needing prior knowledge</li>
    <li>Explore deeper layers of understanding at your own pace</li>
  </ul>
</div>

{/* Conversational Fluency Section */}
<div className="section" style={{ textAlign: "left", maxWidth: "700px", margin: "3rem auto" }}>
  <h2 className="sectionTitle" style={{ textAlign: "left" }}>
    Unlock Conversational Fluency
  </h2>
  <p style={{ lineHeight: "1.6", marginTop: "1rem" }}>
    Before you can speak a new language—academic, professional, or technical—you have to hear it first.
    Our AI hosts model fluent discussions to help you internalize how ideas are explained, challenged,
    and connected.
  </p>
  <ul style={{ marginTop: "1rem", paddingLeft: "1.25rem" }}>
    <li>Hear complex concepts in plain, contextual language</li>
    <li>Absorb field-specific vocabulary naturally</li>
    <li>Build a mental model of the topic without formal study</li>
  </ul>
</div>
</section>


      </main>

      <footer className={styles.footer}>
        <p>© 2025 ForeverFM 🎙️ Always On. Always Learning.</p>
      </footer>
    </div>
  );
}
