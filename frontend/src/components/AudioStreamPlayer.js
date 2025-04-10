"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import styles from "./AudioStreamPlayer.module.css";
import io from "socket.io-client";

export default function AudioStreamPlayer({ audioSrc = `${apiUrl}/audio` }) {
  const [transcript, setTranscript] = useState("");
  const [position, setPosition] = useState({ elapsed: 0, duration: 0 });
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const audioContextRef = useRef(null);
  const socketRef = useRef(null);
  const queueRef = useRef([]); // Queue of decoded AudioBuffers
  const currentSourceRef = useRef(null);
  const startTimeRef = useRef(null);
  const offsetTimeRef = useRef(0);
  const gainNodeRef = useRef(null);

  // const audioRef = useRef(null);
  const [volume, setVolume] = useState(1);

  const togglePlayback = () => {
    if (audioContextRef?.current?.state === "suspended") {
      audioContextRef.current.resume();
    }
    
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
      setIsReady(true);
    }
  
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
    if (!audioContextRef.current || queueRef.current.length === 0 || !isPlaying) return;
  
    const buffer = queueRef.current.shift();
    const source = audioContextRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(gainNodeRef.current);
  
    source.onended = () => {
      currentSourceRef.current = null;
      playNextInQueue(); // continue
    };
  
    source.start(0);
    currentSourceRef.current = source;
    startTimeRef.current = audioContextRef.current.currentTime;
  };
  

  useEffect(() => {
    // Connect to the WebSocket server
    socketRef.current = io(`${apiUrl}`, {
      transports: ["websocket"],
      forceNew: true,
    });

    socketRef.current.on("connect", () => {
      console.log("Connected to WebSocket");
    });

    socketRef.current.on("new_file", (data) => {
      console.log("New audio file:", data.file);
    });

    socketRef.current.on("audio", (data) => {
      console.log("Received audio event");
    
      if (data instanceof Blob) {
        // If it's a Blob (unlikely with socket.io), convert to ArrayBuffer
        data.arrayBuffer().then((arrayBuffer) => {
          decodeAndQueue(arrayBuffer);
        });
      } else if (data.data && data.data instanceof ArrayBuffer) {
        decodeAndQueue(data.data);
      } else if (data.data && data.data.buffer) {
        // Likely a Uint8Array from backend raw bytes (your case)
        decodeAndQueue(data.data.buffer);
      } else {
        console.warn("Unrecognized audio data format", data);
      }
    });
    
    function decodeAndQueue(arrayBuffer) {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        gainNodeRef.current = audioContextRef.current.createGain();
        gainNodeRef.current.connect(audioContextRef.current.destination);
        setIsReady(true);
      }
    
      audioContextRef.current.decodeAudioData(arrayBuffer)
        .then((decodedBuffer) => {
          console.log("Decoded audio buffer");
          queueRef.current.push(decodedBuffer);
          if (isPlaying && !currentSourceRef.current) {
            playNextInQueue();
          }
        })
        .catch((err) => {
          console.error("Audio decode error:", err);
        });
    }
    

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
  }, [isPlaying, playNextInQueue]);

  // Effect to manage playback state
  useEffect(() => {
    if (isReady && isPlaying) {
      playNextInQueue();
    }
  }, [isReady, isPlaying, playNextInQueue]);

  // useEffect(() => {
  //   if (audioRef.current) {
  //     audioRef.current.volume = volume;
  //     if (isPlaying) {
  //       audioRef.current.play().catch(console.error);
  //     } else {
  //       audioRef.current.pause();
  //     }
  //   }
  // }, [isPlaying, volume]);

  return (
    <div className={styles.player}>
      {/* <audio ref={audioRef} src={audioSrc} autoPlay loop /> */}

      <div className={styles.controls}>
        <button onClick={togglePlayback} className={styles.button}>
          <Image
            src={isPlaying ? "/stream-pause.svg" : "/stream-play.svg"}
            alt={isPlaying ? "Pause" : "Play"}
            width={18}
            height={18}
            style={{ filter: "invert(1)" }}
          />
        </button>

        <button onClick={toggleMuted} className={styles.button}>
          <Image
            src={!isMuted ? "/volume-high.svg" : "/volume-slash.svg"}
            alt={!isMuted ? "Volume on" : "Muted"}
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
            const newVolume = parseFloat(e.target.value);
            setVolume(newVolume);
            if (gainNodeRef.current) {
              gainNodeRef.current.gain.setValueAtTime(newVolume, audioContextRef.current.currentTime);
            }
            setIsMuted(newVolume < 0.1);
          }}
          className={styles.slider}
        />
      </div>
{/*      <p>
        {Math.floor(position.elapsed / 60)}:{String(Math.floor(position.elapsed % 60)).padStart(2, '0')} / 
        {Math.floor(position.duration / 60)}:{String(Math.floor(position.duration % 60)).padStart(2, '0')}
      </p>*/}
    </div>
  );
}