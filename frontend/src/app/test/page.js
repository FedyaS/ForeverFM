"use client";

import { useEffect, useRef, useState } from "react";
import io from "socket.io-client";

export default function AudioPlayer() {
  const [transcript, setTranscript] = useState("");
  const [position, setPosition] = useState({ elapsed: 0, duration: 0 });

  const audioContextRef = useRef(null);
  const socketRef = useRef(null);
  const queueRef = useRef([]); // Queue of decoded AudioBuffers
  const isPlayingRef = useRef(false);
  const currentSourceRef = useRef(null);
  const startTimeRef = useRef(null);

  const playNextInQueue = () => {
    if (queueRef.current.length === 0 || isPlayingRef.current) return;

    const buffer = queueRef.current.shift();
    const source = audioContextRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContextRef.current.destination);

    source.onended = () => {
      isPlayingRef.current = false;
      playNextInQueue(); // Play the next audio if available
    };

    source.start(0);
    currentSourceRef.current = source;
    startTimeRef.current = audioContextRef.current.currentTime;
    isPlayingRef.current = true;
  };

  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();

    // Connect to the WebSocket server
    socketRef.current = io("http://localhost:5001"); // Use http:// for Socket.IO

    socketRef.current.on("connect", () => {
      console.log("Connected to WebSocket");
    });

    socketRef.current.on("new_file", (data) => {
      console.log("New audio file:", data.file);
    });

    socketRef.current.on("audio", (data) => {
      const audioBinaryData = new Uint8Array(data.data);
      audioContextRef.current.decodeAudioData(audioBinaryData.buffer)
        .then((decodedBuffer) => {
          queueRef.current.push(decodedBuffer);
          playNextInQueue(); // Try playing if not already playing
        })
        .catch((err) => console.error("Audio decode error:", err));
    });

    socketRef.current.on("transcript", (data) => {
      setTranscript(data.data);
    });

    socketRef.current.on("position", (data) => {
      setPosition({ elapsed: data.elapsed_time, duration: data.duration });
    });

    return () => {
      socketRef.current.disconnect();
      if (currentSourceRef.current) {
        currentSourceRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>ForeverFM Player</h1>
      <div>
        <h3>Transcript</h3>
        <p>{transcript || "Waiting for transcript..."}</p>
      </div>
      <div>
        <h3>Playback Position</h3>
        <progress
          value={position.elapsed}
          max={position.duration}
          style={{ width: "100%" }}
        />
        <p>
          {Math.round(position.elapsed)}s / {Math.round(position.duration)}s
        </p>
      </div>
    </div>
  );
}
