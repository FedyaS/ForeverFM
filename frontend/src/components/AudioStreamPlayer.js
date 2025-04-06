"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import styles from "./AudioStreamPlayer.module.css";

export default function AudioStreamPlayer({ audioSrc = "http://localhost:5001/audio" }) {
  const [transcript, setTranscript] = useState("");
  const [position, setPosition] = useState({ elapsed: 0, duration: 0 });
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [volume, setVolume] = useState(1);

  const audioRef = useRef(null);
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
    if (isPlaying && !isMuted) {
      gainNodeRef.current.gain.setValueAtTime(0, audioContextRef.current.currentTime); // mute
      setIsPlaying(false);
    } else if (!isMuted) {
      gainNodeRef.current.gain.setValueAtTime(1, audioContextRef.current.currentTime); // unmute
      setIsPlaying(true);
      offsetTimeRef.current = position.elapsed;
      playNextInQueue();
    } else if (isPlaying && isMuted) {
      gainNodeRef.current.gain.setValueAtTime(0, audioContextRef.current.currentTime); // unmute
      setIsPlaying(false);
      setIsMuted(false);
      offsetTimeRef.current = position.elapsed;
      playNextInQueue();
    }
  }; 
  
  const toggleMuted = () => {
    if (!isMuted && isPlaying) {
      setVolume(0);
      gainNodeRef.current.gain.setValueAtTime(0, audioContextRef.current.currentTime); // mute
      setIsMuted(true);
    } else if (isPlaying) {
      setVolume(1);
      gainNodeRef.current.gain.setValueAtTime(1, audioContextRef.current.currentTime); // unmute
      setIsMuted(false);
      offsetTimeRef.current = position.elapsed;
      playNextInQueue();
    }
  }

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

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
      if (isPlaying) {
        audioRef.current.play().catch(console.error);
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, volume]);

  return (
    <div className={styles.player}>
      <audio ref={audioRef} src={audioSrc} autoPlay loop />

      <div className={styles.controls}>
        <button onClick={() => setIsPlaying(!isPlaying)} className={styles.button}>
          <Image
            src={isPlaying ? "/stream-pause.svg" : "/stream-play.svg"}
            alt={isPlaying ? "Pause" : "Play"}
            width={18}
            height={18}
            style={{ filter: "invert(1)" }}
          />
        </button>

        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={volume}
          onChange={(e) => {
            setVolume(parseFloat(e.target.value))
            if (volume >= 0.2) setIsMuted(false)
            if (volume < 0.2) {
              setIsMuted(true)
              gainNodeRef.current.gain.setValueAtTime(0, audioContextRef.current.currentTime);
            } else if (isPlaying) {
              gainNodeRef.current.gain.setValueAtTime(volume, audioContextRef.current.currentTime);
          }}}
          className={styles.slider}
        />

        <button onClick={toggleMuted} className={styles.button}>
          <Image
            src={!isMuted ? "/volume-high.svg" : "/volume-slash.svg"}
            alt={!isMuted ? "Volume on" : "Muted"}
            width={18}
            height={18}
            style={{ filter: "invert(1)" }}
          />
        </button>
      </div>
    </div>
  );
}
