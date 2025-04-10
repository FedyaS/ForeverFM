"use client";
import ChatBox from "../../components/ChatBox";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import styles from "../styles/page.module.css";
import Avatars from "../../components/Avatar";
import AudioStreamPlayer from "../../components/AudioStreamPlayer";
import Description from "../../components/Description";

const apiUrl = process.env.NEXT_PUBLIC_API_URL;

export default function Stream() {

  return (
    <div className={styles.page} style={{ width: "100%", maxWidth: "1200px", margin: "0 auto" }}>
      <main className={styles.main} style={{ width: "100%", gap: "1rem" }}>
        {/* Header */}
        <div style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.5rem"
        }}>
          <h1 className={styles.title} style={{ textAlign: "left", marginBottom: "0" }}>
            ForeverFM: AI Podcast Stream
          </h1>
          <p style={{ color: "#f44", fontWeight: "bold" }}>🔴 Live now</p>
        </div>

        {/* Stream + Chat layout */}

        <div className={styles.streamLayout}>
          <div className={styles.streamContent}>

            <Image
              src="/av-stock-photo.png"
              alt="Podcast simulation"
              width={400}
              height={400}
              className={styles.responsiveImage}
            />

              <AudioStreamPlayer audioSrc={`${apiUrl}/audio`} />
          </div>

          <div className={styles.chatWrapper}>
            <ChatBox />
            
          </div>

        </div>
        
        {/* Avatar Widget */}
        <div style={{ marginTop: "1rem", marginBottom: "1rem", display: "-webkit-flex",  justifyContent: "space-between",}}> {/* TODO: Restructure divs to avoid this*/}
          <Avatars />
          <Description />
        </div>

        {/* Navigation */}
        <div className={styles.ctas} style={{ marginTop: "2rem" }}>
          <Link href="/" className={styles.primary}>
            ← Back to Home
          </Link>
        </div>
      </main>

      <footer className={styles.footer}>
        <p>© 2025 ForeverFM🎙️</p>
      </footer>
    </div>
  );
}