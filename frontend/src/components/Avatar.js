"use client";
import Image from "next/image";
import styles from "./Avatar.module.css";

export default function Avatars() {
  const avatars = [
    {
      name: "Aaliyah",
      src: "/avatar1.png",
      role: "Tech Analyst",
      tags: ["AI", "ML", "Prompting", "Systems", "Live"]
    },
    {
      name: "Chip",
      src: "/avatar2.png",
      role: "Culture Curator",
      tags: ["Trends", "Media", "Society", "Narrative", "Replay"]
    }
  ];

  return (
    <div className={styles.wrapper}>
      {avatars.map((a) => (
        <div key={a.name} className={styles.card}>
          {/* Avatar + Live */}
          <div className={styles.avatarBox}>
            <Image
              src={a.src}
              alt={a.name}
              width={56}
              height={56}
              className={styles.avatarImage}
            />
            <div className={styles.liveBadge}>LIVE</div>
          </div>

          {/* Info + Tags Split */}
          <div className={styles.mainContent}>
            <div className={styles.info}>
              <div className={styles.nameLine}>
                {a.name} <span className={styles.check}>✔</span>
              </div>
              <div className={styles.role}>{a.role}</div>
            </div>

            <div className={styles.tags}>
              {a.tags.map(tag => (
                <span key={tag} className={styles.tag}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
