import styled, { keyframes } from "styled-components";

const Robot = () => (
  <Wrapper>
    <div className="scene">
      {/* Core orb */}
      <div className="orb" />
      {/* Orbital rings */}
      <div className="ring ring1" />
      <div className="ring ring2" />
      <div className="ring ring3" />
      {/* Floating data dots */}
      {[...Array(8)].map((_, i) => (
        <div key={i} className={`dot dot${i + 1}`} />
      ))}
    </div>
    <p className="label">AI · PostgreSQL · MongoDB</p>
  </Wrapper>
);

/* ── Keyframes ───────────────────────────────────────────────────────────── */

const pulse = keyframes`
  0%, 100% { transform: scale(1);   opacity: 0.9; }
  50%       { transform: scale(1.08); opacity: 1;   }
`;

const spinCW = keyframes`
  from { transform: rotateX(70deg) rotateZ(0deg); }
  to   { transform: rotateX(70deg) rotateZ(360deg); }
`;

const spinCCW = keyframes`
  from { transform: rotateX(70deg) rotateZ(0deg); }
  to   { transform: rotateX(70deg) rotateZ(-360deg); }
`;

const spinFlat = keyframes`
  from { transform: rotateX(20deg) rotateZ(0deg); }
  to   { transform: rotateX(20deg) rotateZ(360deg); }
`;

const float = keyframes`
  0%, 100% { transform: translateY(0px);  }
  50%       { transform: translateY(-12px); }
`;

const blink = keyframes`
  0%, 80%, 100% { opacity: 0; }
  40%           { opacity: 1; }
`;

/* ── Styled component ────────────────────────────────────────────────────── */

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 500px;
  perspective: 600px;

  .scene {
    position: relative;
    width: 260px;
    height: 260px;
    animation: ${float} 4s ease-in-out infinite;
  }

  /* Central glowing orb */
  .orb {
    position: absolute;
    top: 50%; left: 50%;
    width: 90px; height: 90px;
    margin: -45px 0 0 -45px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #47C9FF, #FF6464 60%, #FFBF59);
    box-shadow:
      0 0 30px 8px rgba(71, 201, 255, 0.4),
      0 0 60px 20px rgba(255, 100, 100, 0.2);
    animation: ${pulse} 3s ease-in-out infinite;
    z-index: 3;
  }

  /* Orbital rings */
  .ring {
    position: absolute;
    top: 50%; left: 50%;
    border-radius: 50%;
    border: 2px solid transparent;
  }

  .ring1 {
    width: 160px; height: 160px;
    margin: -80px 0 0 -80px;
    border-color: rgba(71, 201, 255, 0.6);
    box-shadow: 0 0 8px rgba(71, 201, 255, 0.3);
    animation: ${spinCW} 5s linear infinite;
  }

  .ring2 {
    width: 210px; height: 210px;
    margin: -105px 0 0 -105px;
    border-color: rgba(255, 100, 100, 0.5);
    box-shadow: 0 0 8px rgba(255, 100, 100, 0.2);
    animation: ${spinCCW} 7s linear infinite;
  }

  .ring3 {
    width: 255px; height: 255px;
    margin: -127px 0 0 -127px;
    border-color: rgba(255, 191, 89, 0.4);
    box-shadow: 0 0 6px rgba(255, 191, 89, 0.15);
    animation: ${spinFlat} 11s linear infinite;
  }

  /* Floating data dots */
  .dot {
    position: absolute;
    border-radius: 50%;
    animation: ${blink} 2.4s ease-in-out infinite;
  }

  .dot1  { width: 8px;  height: 8px;  background: #47C9FF; top: 10%;  left: 48%; animation-delay: 0s;    }
  .dot2  { width: 6px;  height: 6px;  background: #FF6464; top: 25%;  left: 80%; animation-delay: 0.3s;  }
  .dot3  { width: 5px;  height: 5px;  background: #FFBF59; top: 60%;  left: 88%; animation-delay: 0.6s;  }
  .dot4  { width: 7px;  height: 7px;  background: #47C9FF; top: 82%;  left: 60%; animation-delay: 0.9s;  }
  .dot5  { width: 6px;  height: 6px;  background: #FF6464; top: 80%;  left: 28%; animation-delay: 1.2s;  }
  .dot6  { width: 5px;  height: 5px;  background: #FFBF59; top: 55%;  left: 8%;  animation-delay: 1.5s;  }
  .dot7  { width: 8px;  height: 8px;  background: #47C9FF; top: 28%;  left: 14%; animation-delay: 1.8s;  }
  .dot8  { width: 6px;  height: 6px;  background: #FF6464; top: 8%;   left: 30%; animation-delay: 2.1s;  }

  .label {
    margin-top: 24px;
    color: #555;
    font-size: 0.8rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }
`;

export default Robot;
