import Link from "next/link";
import Image from "next/image";
import styles from "../styles/page.module.css";

export default function About() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        {/* Hero */}
        <section style={{ textAlign: "center" }}>

          <h1 className={styles.title}>The Forever Team</h1>

          <div className={styles.imageContainer}>
            <Image
              src="/About-Photo-Styled.png"
              alt="ForeverFM Team"
              width={250}
              height={250}
              className={`${styles.teamPhoto} ${styles.primary}`}
              priority
            />
          </div>

          <Image
              src="/ForeverFM Microphone Icon.png"
              alt="Podcast simulation"
              width={25}
              height={35}
            />


          <p style={{ marginTop: "1rem", fontWeight: "500" }}>
            Just Four Beaverhackers
          </p>
          
        </section>

        {/* Story */}
        <section style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p className={styles.description}>
          ForeverFM is a collaborative experiment born at Oregon State University's 🦫 BeaverHacks—where four students came together to explore the frontier of AI-driven storytelling.
          We're exploring the frontier of language models, voice synthesis, and the vibe of collaborative creativity.
          </p>

          <p className={styles.description}>
            Huge thanks to the event organizers and sponsors who made BeaverHacks possible. Without your support, this project—and this team—wouldn’t exist.
          </p>

          <p className={styles.description} style={{ fontStyle: "italic" }}>
            Signing off with optimism, determination, and growth—  
            <br />
            —The ForeverFM Team <span style={{ fontStyle: "normal" }}> 🎙️</span>
          </p>
          
        </section>

      
        {/* CTA */}
        <div className={styles.ctas}>
          <Link href="/" className={styles.primary}>
            ← Back to Home
          </Link>
        </div>
      </main>

      <footer className={styles.footer}>
        <p>© 2025 ForeverFM 🎙️</p>
      </footer>
    </div>
  );
}
