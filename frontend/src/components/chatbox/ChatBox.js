import React, { useState, useRef } from "react";
import { FaMicrophone, FaStop } from 'react-icons/fa';

const ChatBox = ({ onSendMessage }) => {
  const [textInput, setTextInput] = useState('');
  // const audioInput = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  // const [audioChunks, setAudioChunks] = useState([]);
  // const mediaRecorder = useRef(null);

  const handleTextChange = (event) => {
    setTextInput(event.target.value);
  };

  const handleStartRecording = async () => {
    // try {
    //   const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    //   const recorder = new MediaRecorder(stream);
    //   mediaRecorder.current = recorder; // Store MediaRecorder instance in useRef

    //   recorder.ondataavailable = (event) => {
    //     if (event.data.size > 0) {
    //       setAudioChunks((prev) => [...prev, event.data]);
    //     }
    //   };

    //   recorder.onstop = () => {
    //     stream.getTracks().forEach(track => track.stop());
    //   };

    //   recorder.start();
    //   setIsRecording(true);
    // } catch (error) {
    //   console.error('Error accessing microphone:', error);
    //   setIsRecording(false);
    // }

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'vi-VN';  // Đặt ngôn ngữ là tiếng Việt
    recognition.interimResults = false; // Không lấy kết quả tạm thời
    recognition.maxAlternatives = 1;  // Giới hạn số kết quả trả về

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setTextInput(transcript);  // Gán kết quả nhận diện giọng nói vào textInput
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();  // Bắt đầu nhận diện giọng nói
  };

  const handleStopRecording = () => {
    // if (mediaRecorder.current) {
    //   mediaRecorder.current.stop();
    //   setIsRecording(false);
    // }

    setIsRecording(false); //Ko can thiet
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    // let audioBlob = null;
    // if (audioChunks.length > 0) {
    //   audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    //   setAudioChunks([]);
    // }

    // if (!textInput && !audioBlob) return;
    if (!textInput) return;

    const formData = new FormData();
    if (textInput) formData.append('text_input', textInput);
    // if (audioBlob) {
    //   const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' })
    //   formData.append('audio_input_file', audioFile);
    // }

    onSendMessage(formData);
    setTextInput('');
    // audioInput.current = null;
  };

  return (
    <>
      <div className="chat_box border-2 border-primary border-top d-flex p-4">
        <form className="w-100 d-flex" onSubmit={handleSubmit}>
          <div className="w-100">
            <textarea className="message border-primary focus-ring focus-ring-primary rounded-3 w-100 px-2 py-1 mt-1 mb-1" type="text"
              placeholder="Nhập câu hỏi ở đây..." value={textInput}
              onChange={handleTextChange}
              style={{ resize: 'vertical', height: "38px" }}
            />

            <div className="d-flex align-items-center">
              {isRecording ? (
                <button type="button" className="btn btn-danger" onClick={handleStopRecording}>
                  <FaStop />
                </button>
              ) : (
                <button type="button" className="btn btn-outline-secondary px-1 py-0 pb-1" onClick={handleStartRecording}>
                  <FaMicrophone />
                </button>
              )}
            </div>

            {/* <button className="border-0 bg-light">
              <i class="fa-solid fa-microphone col-1"></i>
            </button> */}
          </div>

          {/* btn submit */}
          <button className="border rounded-3 ms-2 bg-primary bg-gradient text-white" type="submit" style={{ width: "50px", height: "56px" }}>
            <i class="fa-solid fa-paper-plane" style={{fontSize: "13px"}}></i>
            <span style={{fontSize: "14px"}}> Gửi </span>
          </button>
        </form>
      </div>
      <span className="text-center" style={{fontSize: "12px"}}>Thông tin có thể sai. Vui lòng kiểm tra kỹ trước khi tin tưởng.</span>
    </>
  );
};

export default ChatBox;