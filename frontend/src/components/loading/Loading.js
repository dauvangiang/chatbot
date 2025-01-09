import logo from '../../assets/bot_icon.png'
import React from 'react'
import '../../App.css';

const Loading = () => {
  return (
    <>
      <div className="loading-animation ms-2">
        <img
          src={logo}
          alt="Loading 1"
          className="loading-image animation-1"
        />
        <img
          src={logo}
          alt="Loading 2"
          className="loading-image animation-2"
        />
        <img
          src={logo}
          alt="Loading 3"
          className="loading-image animation-3"
        />
      </div>
    </>
  );
};

export default Loading;