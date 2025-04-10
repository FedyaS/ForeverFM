import { useEffect, useState } from 'react';
import Header from '../components/header';
import AudioPlayer from '../components/AudioPlayer';
import ChatPanel from '../components/ChatPanel';
import '../styles/globals.css';

const apiUrl = process.env.NEXT_PUBLIC_API_URL;

export default function Home() {
  const [chatMessages, setChatMessages] = useState([]);
  const [username, setUsername] = useState('User_' + Math.floor(Math.random() * 1000));

  // Fetch initial chat messages
  useEffect(() => {
    fetchMessages();
    // Poll for new messages every 3 seconds
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchMessages = async () => {
    try {
      const response = await fetch(`${apiUrl}/chat`);
      const data = await response.json();
      setChatMessages(data.messages);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const sendMessage = async (messageText) => {
    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          message: messageText,
          timestamp: new Date().toISOString(),
        }),
      });
      
      if (response.ok) {
        fetchMessages(); // Refresh messages after sending
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div className="container">
      {/* Background video */}
      <video autoPlay muted loop className="background-video">
        <source src="/video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      
      <div className="content">
        <Header podcastTitle="Tech Talk Live" />
        <AudioPlayer audioSrc={`${apiUrl}/audio`} />
        <ChatPanel 
          messages={chatMessages} 
          username={username}
          onSendMessage={sendMessage}
        />
      </div>
    </div>
  );
}