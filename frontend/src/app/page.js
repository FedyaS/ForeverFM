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
    bgColor: "#7B3F00",
    image: "/categories/category-gaming.svg",
  },
  {
    name: "Technology",
    slug: "technology",
    description: "AI, software, gadgets, and how it all connects.",
    bgColor: "#005F73",
    image: "/categories/category-tech.svg",
  },
  {
    name: "Finance",
    slug: "finance",
    description: "Markets, money, investing, and economic ideas.",
    bgColor: "#264653",
    image: "/categories/category-finance.svg",
  },
  {
    name: "Health & Wellness",
    slug: "health",
    description: "Fitness, mental wellness, nutrition, and biohacking.",
    bgColor: "#2A9D8F",
    image: "/categories/category-health.svg",
  },
  {
    name: "Real Estate",
    slug: "real-estate",
    description: "Housing, land, and future trends in living spaces.",
    bgColor: "#E76F51",
    image: "/categories/category-real-estate.svg",
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
                <div key={topic.slug} className="card">
                  <div className="thumbnail" style={{ backgroundColor: topic.bgColor }}>
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
    letting you dive deep or stay casual—all based on your curiosity. Whether it's finance, tech,
    wellness, or gaming, you're just one click away from immersive learning.
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
