"use client";
import { useState, useEffect, useRef } from "react";
import styles from "./ChatBox.module.css";

export default function ChatBox() {
  const [userPrompt, setUserPrompt] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      username: "Host",
      message: "Welcome to the livestream! Feel free to join the chat.",
      timestamp: "13:45",
    },
    {
      id: 2,
      username: "Moderator",
      message: "Remember to keep the chat respectful and on topic.",
      timestamp: "14:10",
    },
  ]);
  const chatRef = useRef(null);
  const username = "User_573";

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userPrompt.trim()) return;

    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const newMessage = {
      id: Date.now(),
      username,
      message: userPrompt.trim(),
      timestamp: time,
    };

    setMessages((prev) => [...prev, newMessage]);
    setIsSubmitting(true);
    setStatusMessage("");

    try {
      const response = await fetch("http://localhost:5000/chat-prompt", {
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
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

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
