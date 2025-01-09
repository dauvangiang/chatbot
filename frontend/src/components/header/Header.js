import React from "react";

import bot_icon from '../../assets/bot_icon.png'
import school_icon from '../../assets/65.png'

const Header = ({setIsInit}) => {
  const handleNewChat = async () => {
    setIsInit(true)
  }
  return (
    <>
      <div class="masthead shadow mb-auto border-bottom pb-2">
        <div class="inner d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center" >
            <img className="school-image rounded-3 ms-2 me-2" src={school_icon} alt="School avatar" style={{width: "50px"}}/>
            <img className="bot-image rounded-3 ms-2 me-2" src={bot_icon} alt="Bot avatar" style={{width: "50px"}}/>
            <h3 class="masthead-brand m-0">AI Mentors</h3>
          </div>
          <nav class="nav nav-masthead justify-content-center">
            <button className="border-0 text-primary bg-white me-1" onClick={handleNewChat}><i class="fa-solid fa-pen-to-square"></i> Cuộc trò chuyện mới</button>
          </nav>
        </div>
      </div>
    </>
  );
}

export default Header;