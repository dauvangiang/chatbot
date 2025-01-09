import React, { useState, useRef } from 'react';
import axios from 'axios';
import Header from './components/header/Header';
import Body from './components/body/Body';
import bot_icon from './assets/bot_icon.png'
import ChatBox from './components/chatbox/ChatBox';
import Loading from './components/loading/Loading';

import school_icon from './assets/65.png'

function App() {
  const [chats, setChats] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null)
  const chatBodyRef = useRef(null);
  const [loading, setLoading] = useState(false);

  const API_ENDPOINT = 'http://127.0.0.1:8000/chat/';
  const MEMORY_ENDPOINT = 'http://127.0.0.1:8000/refresh_memory/';

  const handleNewChat = async () => {
    try {
      await axios.get(MEMORY_ENDPOINT);
      setChats([]);
    } catch (error) {
      console.error('Error clearing memory', error)
    }
  }

  const scrollToBottom = () => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  };

  const handleSendMessage = async (formData) => {
    const userMessage = formData.get("text_input") || "Voice chat...";
    setChats(prevChats => [...prevChats, { text: userMessage, isUser: true }]);
    // scrollToBottom();
    setLoading(true);
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
      setChats(prevChats => [...prevChats, {
        text: "Có lỗi xảy ra, vui lòng thử lại.",
        isUser: false,
        audioUrl: null
      }])
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <>
      <div className="p-3" style={{ height: "100vh" }}>
        {/* Header */}
        <div class="masthead shadow mb-auto border-bottom pb-2">
          <div class="inner d-flex justify-content-between align-items-center">
            <div className="d-flex align-items-center" >
              <img className="school-image border border-primary border-2 rounded-5 ms-2 px-1 py-2" src={school_icon} alt="School avatar" style={{ width: "60px" }} />
              <img className="bot-image rounded-3 ms-2 me-2 border border-2 border-primary" src={bot_icon} alt="Bot avatar" style={{ width: "46px" }} />
              <h3 class="masthead-brand m-0">AI Mentors</h3>
            </div>
            <nav class="nav nav-masthead justify-content-center">
              <button className="border-0 text-primary bg-white me-1" onClick={handleNewChat}><i class="fa-solid fa-pen-to-square"></i> Cuộc trò chuyện mới</button>
            </nav>
          </div>
        </div>

        {/* Body */}
        {
          chats.length == 0
            ? (
              <div className="d-flex flex-column mt-3 ms-3 me-3" style={{ height: "85vh" }}>
                <div className="d-flex flex-column align-items-center m-auto">
                  <img className="border border-5 border-primary rounded-circle mb-2" style={{ width: "97px" }} src={bot_icon}></img>
                  <strong>Tôi có thể giúp gì cho bạn?</strong>
                </div>
                <ChatBox onSendMessage={handleSendMessage} />
              </div>
            )
            : (
              <div className="d-flex flex-column shadow mt-3 ms-3 me-3" style={{ height: "87vh" }}>
                <div className="chat_body flex-grow-1 overflow-auto p-4" ref={chatBodyRef}>
                  {chats.map((chat, index) => {
                    if (loading && index == chats.length - 1 && chat.isUser) {
                      return (
                        <>
                          <div key={index} className="user_input ms-auto bg-primary bg-gradient text-white mb-4 border rounded-2 py-1 px-2" style={{ maxWidth: "420px", width: "fit-content" }}>
                            {chat.text}
                          </div>
                          <Loading />
                        </>
                      )
                    }
                    if (chat.isUser) {
                      return (
                        <div key={index} className="user_input ms-auto bg-primary bg-gradient text-white mb-4 border rounded-2 py-1 px-2" style={{ maxWidth: "420px", width: "fit-content" }}>
                          {chat.text}
                        </div>
                      )
                    } else {
                      return (<ChatOutput key={index} chat={chat} playAudio={playAudio} />)
                    }
                  })
                  }
                </div>

                {/* Chatbox */}
                <ChatBox onSendMessage={handleSendMessage} />
              </div>
            )
        }
      </div>
    </>
  );

  // return (
  //   <>
  //     <div className="p-3" style={{height: "100vh"}}>
  //       <Header setIsInit={setIsInit}/>
  //       <Body isInit={isInit} setIsInit={setIsInit}/>
  //     </div>
  //   </>
  // );
};

const ChatOutput = ({ chat, playAudio }) => {
  const text = chat.text;
  const audioPath = chat.audioPath;
  const base64Img1 = chat.images[0] || null;
  const base64Img2 = chat.images[1] || null;
  const audioRef = chat.audioRef;
  const setIsPlaying = chat.setIsPlaying;
  const [playing, setPlaying] = useState(false);

  const play = (text) => {
    // const speakText = (text) => {
    //   const utterance = new SpeechSynthesisUtterance(text);
    //   utterance.lang = 'vi-VN';  // Đặt ngôn ngữ là tiếng Việt (hoặc ngôn ngữ khác)
    //   speechSynthesis.speak(utterance);
    // };

    // speakText(text);
    if (speechSynthesis.speaking || speechSynthesis.paused) {
      speechSynthesis.cancel(); // Dừng nếu đang phát hoặc tạm dừng
      setPlaying(false);
      return;
    }
    setPlaying(true);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'vi-VN'; // Đặt ngôn ngữ
    speechSynthesis.speak(utterance);
    setPlaying(false);
  }

  const openFullScreen = (src) => {
    const imgWindow = window.open('', '', 'width=800,height=600');
    imgWindow.document.write(`<img src="${src}" style="width: 100%; height: auto;" />`);
  };

  const downloadImage = (src) => {
    const link = document.createElement('a');
    link.href = src;
    link.download = 'image.png';
    link.click();
  };

  return (
    <>
      <div className="bot_output d-flex mb-4 border rounded-2 bg-body-secondary text-black p-1" style={{ minWidth: "320px", maxWidth: "600px", width: "fit-content" }}>
        <img className="me-1 rounded-4" src={bot_icon} style={{ width: "28px", height: "28px" }}></img>
        <div className="output">
          <div className="">{text}</div>

          {/* Audio */}
          {playing ? (
            <div className="p-1 mb-1" style={{ cursor: "pointer" }} onClick={() => speechSynthesis.cancel()}>
              <i className="fa-solid fa-volume-xmark" style={{ fontSize: "12px" }}></i>
            </div>
          )
            : (
              <div className="p-1 mb-1" style={{ cursor: "pointer" }} onClick={e => play(text)}>
                <i class="fa-solid fa-volume-high" style={{ fontSize: "12px" }}></i>
              </div>
            )}

          <div className="references_imgs d-flex">
            {base64Img1 ? (
              <div className="border border-success border-2 p-2 rounded-2 me-2 position-relative">
                <img
                  src={`data:image/png;base64,${base64Img1}`}
                  alt="Ảnh minh họa 1" style={{ width: "120px" }}
                  onClick={() => openFullScreen(`data:image/png;base64,${base64Img1}`)}
                />
                <i
                  class="fa-solid fa-download position-absolute"
                  style={{ right: "10px", bottom: "10px", cursor: "pointer", fontSize: "12px" }}
                  onClick={() => downloadImage(`data:image/png;base64,${base64Img1}`)}
                ></i>
              </div>
            ) : (<></>)}
            {base64Img2 ? (
              <div className="border border-success border-2 p-2 rounded-2 position-relative">
                <img
                  src={`data:image/png;base64,${base64Img2}`}
                  alt="Ảnh minh họa 2" style={{ width: "120px" }}
                  onClick={() => openFullScreen(`data:image/png;base64,${base64Img2}`)}
                />
                <i
                  class="fa-solid fa-download position-absolute"
                  style={{ right: "10px", bottom: "10px", cursor: "pointer", fontSize: "12px" }}
                  onClick={() => downloadImage(`data:image/png;base64,${base64Img2}`)}
                ></i>
              </div>
            ) : (<></>)}
          </div>
        </div>
      </div>
    </>
  );
};

export default App;