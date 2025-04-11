"use client";
import { useState, useEffect, useRef } from "react";
import styles from "./ChatBox.module.css";
import Cookies from "js-cookie";

const MAX_TOKENS = 5;
const COOKIE_KEY = "usedTokens";
const COOKIE_TIMESTAMP = "lastTokenReset";
const apiUrl = process.env.NEXT_PUBLIC_API_URL;

export default function ChatBox() {
  const [userPrompt, setUserPrompt] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tokens, setTokens] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: 1,
      username: "Host",
      message: "Welcome to the livestream! Feel free to join the chat.",
      timestamp: "01:45 PM",
    },
    {
      id: 2,
      username: "Moderator",
      message: "Remember to keep the chat respectful and on topic.",
      timestamp: "02:10 PM",
    },
  ]);
  const chatRef = useRef(null);
  const username = "User_573";

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userPrompt.trim()) return;

    if (tokens <= 0) {
      setStatusMessage("Come back tomorrow for more!");
      return;
    }

    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const newMessage = {
      id: Date.now(),
      username,
      message: userPrompt.trim(),
      timestamp: time,
    };

    setMessages((prev) => [...prev, newMessage]);

    setUserPrompt("") 
    setTokens((prev) => {
      const newTokens = prev - 1;
      const usedTokens = MAX_TOKENS - newTokens;
    
      Cookies.set(COOKIE_KEY, usedTokens.toString(), { expires: 7 });
    
      // Save timestamp if not already set
      if (!Cookies.get(COOKIE_TIMESTAMP)) {
        Cookies.set(COOKIE_TIMESTAMP, Date.now().toString(), { expires: 7 });
      }
    
      return newTokens;
    });
    setIsSubmitting(true);
    setStatusMessage("");

    try {
      const response = await fetch("http://localhost:5001/chat-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_prompt: userPrompt }),
      });

      const result = await response.json();

      if (response.ok) {
        setStatusMessage(result.message);
        setUserPrompt("");
      } else {
        setStatusMessage(result.message || "Failed to send prompt.");
      }
    } catch (err) {
      console.error(err);
      setStatusMessage("Error sending prompt.");
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    const storedUses = parseInt(Cookies.get(COOKIE_KEY) || "0", 10);
    const lastReset = Cookies.get(COOKIE_TIMESTAMP);
    const now = Date.now();
  
    if (lastReset && now - parseInt(lastReset, 10) > 24 * 60 * 60 * 1000) {
      // More than 24h has passed — reset
      Cookies.set(COOKIE_TIMESTAMP, now.toString());
      Cookies.set(COOKIE_KEY, "0");
      setTokens(MAX_TOKENS);
    } else {
      const remaining = Math.max(0, MAX_TOKENS - storedUses);
      setTokens(remaining);
    }
  }, []);
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  if (tokens == null) return null;

  return (
    <div className={styles.wrapper}>
      {/* Header */}
      <div className={styles.header}>
        Live Chat<br />
        <span>You: <span style={{ color: "#55ff99" }}>{username}</span></span>
      </div>

      {/* Message list */}
      <div ref={chatRef} className={styles.messageList}>
        {messages.map((msg) => (
          <div key={msg.id} className={styles.message}>
            <div className={styles.messageHeader}>
              <span><strong>{msg.username}</strong></span>
              <span className={styles.timestamp}>{msg.timestamp}</span>
            </div>
            <div>{msg.message}</div>
          </div>
        ))}
      </div>

      {/* Form with embedded button */}
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          id="chat-input"
          name="chat"
          className={styles.input}
          placeholder="Say something..."
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          disabled={isSubmitting}
        />
        <button
          type="submit"
          className={styles.button}
          disabled={isSubmitting}
        >
          Chat
        </button>
      </form>

      {/* Status message */}
      {statusMessage && (
        <p className={styles.status}>{statusMessage}</p>
      )}
    </div>
  );
}
