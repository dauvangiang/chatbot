import React, { useState, useRef } from "react";
import bot_icon from '../../assets/bot_icon.png'
import ChatBox from "../chatbox/ChatBox";
import axios from "axios";

const Body = ({ isInit, setIsInit }) => {
  const [chats, setChats] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null)
  const chatBodyRef = useRef(null); // Tạo ref để tham chiếu đến phần tử cuộn được

  const API_ENDPOINT = 'http://localhost:8000/chat/';
  const MEMORY_ENDPOINT = 'http://localhost:8000/refresh_memory/';

  const handleSendMessage = async (formData) => {
    const userMessage = formData.get("text_input") || "Audio message...";
    setChats(prevChats => [...prevChats, { text: userMessage, isUser: true }]);
    scrollToBottom();
    try {
      const response = await axios.post(API_ENDPOINT, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const responseData = response.data;
      const botMessage = {
        text: responseData.answer,
        isUser: false,
        audioUrl: responseData.audio_url,
        images: []
      }
      if (responseData.image_1_base64) {
        botMessage.images.push(responseData.image_1_base64)
      }
      if (responseData.image_2_base64) {
        botMessage.images.push(responseData.image_2_base64)
      }

      setChats(prevChats => [...prevChats, botMessage]);

    } catch (error) {
      console.error('Error during API call:', error);
      setChats(prevChats => [...prevChats, { text: "Error getting response from server...", isUser: false }])
    }
  };

  const scrollToBottom = () => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight; // Cuộn đến cuối
    }
  };

  const handleNewChat = async () => {
    try {
      // await axios.get(MEMORY_ENDPOINT);
      setChats([]);
    } catch (error) {
      console.error('Error clearing memory', error)
    }
  }

  const playAudio = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  if (chats.length == 0 || !isInit) {
    return (
      <>
        <div className="d-flex flex-column mt-3 bg-light ms-3 me-3" style={{ height: "85vh" }}>
          <div className="d-flex flex-column align-items-center m-auto">
            <img className="border border-5 border-success rounded-circle mb-2" style={{width: "97px"}} src={bot_icon}></img>
            <strong>Tôi có thể giúp gì cho bạn?</strong>
          </div>
          <ChatBox onSendMessage={handleSendMessage} />
        </div>
      </>
    );
  }

  return (
    <>
      <div className="d-flex flex-column mt-3 bg-light ms-3 me-3" style={{ height: "87vh" }}>
        <div className="chat_body flex-grow-1 overflow-auto p-4" ref={chatBodyRef}>
          {chats.map(chat => {
            if (chat.isUser) {
              return (
                <div className="user_input ms-auto bg-primary bg-gradient text-white mb-4 border rounded-2 p-1" style={{ maxWidth: "75%", width: "auto" }}>
                </div>
              )
            } else {
              return (<ChatOutput />)
            }
          })

          }
        </div>
        <ChatBox onSendMessage={handleSendMessage} />
      </div>
    </>
  );
};

const ChatOutput = ({ text, audioPath, base64Img1, base64Img2, playAudio, audioRef, setIsPlaying }) => {
  return (
    <>
      <div className="bot_output d-flex mb-4 border rounded-2 bg-body-secondary text-black p-1" style={{ maxWidth: "75%" }}>
        <img className="me-1 rounded-4" src={bot_icon} style={{ width: "8%", height: "8%", maxWidth: "50px", maxHeight: "50px" }}></img>
        <div className="output">
          <div className="">{text}</div>

          {/* Audio */}
          <div className="p-1" onClick={playAudio}>
            <i class="fa-solid fa-volume-high" style={{ fontSize: "14px" }}></i>
          </div>
          <audio ref={audioRef} src={audioPath} onEnded={() => setIsPlaying(false)} />

          <div className="references_imgs d-flex">
            <div className="border p-2 rounded-2 me-2">
              {base64Img1 ? (
                <img src={`data:image/png;base64,${base64Img1}`} alt="Ảnh minh họa 1" />
              ) : (
                <p>Loading...</p>
              )}
            </div>
            <div className="border p-2 rounded-2">
              {base64Img2 ? (
                <img src={`data:image/png;base64,${base64Img2}`} alt="Ảnh minh họa 2" />
              ) : (
                <p>Loading...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Body;