"use client";

import { useEffect, useRef, useState } from "react";
import io from "socket.io-client";

export default function AudioPlayer() {
  const [transcript, setTranscript] = useState("");
  const [position, setPosition] = useState({ elapsed: 0, duration: 0 });
  const [isPlaying, setIsPlaying] = useState(false);
  const [isReady, setIsReady] = useState(false);
  // test
  const audioContextRef = useRef(null);
  const socketRef = useRef(null);
  const queueRef = useRef([]); // Queue of decoded AudioBuffers
  const currentSourceRef = useRef(null);
  const startTimeRef = useRef(null);
  const offsetTimeRef = useRef(0);
  const gainNodeRef = useRef(null);

  const togglePlayback = () => {
    if (!audioContextRef.current) {
      // Create audio context on first interaction
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
      setIsReady(true);
    }
  
    // Toggle mute instead of stopping the audio
    if (isPlaying) {
      gainNodeRef.current.gain.setValueAtTime(0, audioContextRef.current.currentTime); // mute
      setIsPlaying(false);
    } else {
      gainNodeRef.current.gain.setValueAtTime(1, audioContextRef.current.currentTime); // unmute
      setIsPlaying(true);
      offsetTimeRef.current = position.elapsed;
      playNextInQueue();
    }
  };  

  const playNextInQueue = () => {
    if (queueRef.current.length === 0) return;
  
    const buffer = queueRef.current.shift();
    const source = audioContextRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(gainNodeRef.current); // route through gain node
  
    source.onended = () => {
      playNextInQueue(); // Always continue playback
    };
  
    source.start(0);
    currentSourceRef.current = source;
    startTimeRef.current = audioContextRef.current.currentTime;
  };
  

  useEffect(() => {
    // Connect to the WebSocket server
    socketRef.current = io("http://localhost:5001"); // Use http:// for Socket.IO

    socketRef.current.on("connect", () => {
      console.log("Connected to WebSocket");
    });

    socketRef.current.on("new_file", (data) => {
      console.log("New audio file:", data.file);
    });

    socketRef.current.on("audio", (data) => {
      // Only decode and queue audio if we have an audio context
      if (audioContextRef.current) {
        const audioBinaryData = new Uint8Array(data.data);
        audioContextRef.current.decodeAudioData(audioBinaryData.buffer)
          .then((decodedBuffer) => {
            queueRef.current.push(decodedBuffer);
            if (isPlaying) {
              playNextInQueue(); // Try playing if currently playing
            }
          })
          .catch((err) => console.error("Audio decode error:", err));
      }
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
        //currentSourceRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Effect to manage playback state
  useEffect(() => {
    if (isReady && isPlaying) {
      playNextInQueue();
    }
  }, [isReady, isPlaying]);

  return (
    <div style={{ padding: "20px", maxWidth: "600px", margin: "0 auto" }}>
      <h1>ForeverFM Player</h1>
      <div style={{ marginBottom: "20px" }}>
        <button 
          onClick={togglePlayback}
          style={{
            padding: "10px 20px",
            fontSize: "16px",
            backgroundColor: isPlaying ? "#ff5555" : "#55aa55",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer"
          }}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
        <span style={{ marginLeft: "15px", fontSize: "14px" }}>
          Current time: {Math.floor(position.elapsed / 60)}:{String(Math.floor(position.elapsed % 60)).padStart(2, '0')}
        </span>
      </div>
      <div>
        <h3>Playback Position</h3>
        <div style={{ display: "flex", alignItems: "center" }}>
          <progress
            value={position.elapsed}
            max={position.duration || 100}
            style={{ width: "100%", height: "15px" }}
          />
        </div>
        <p>
          {Math.floor(position.elapsed / 60)}:{String(Math.floor(position.elapsed % 60)).padStart(2, '0')} / 
          {Math.floor(position.duration / 60)}:{String(Math.floor(position.duration % 60)).padStart(2, '0')}
        </p>
      </div>
    </div>
  );
}