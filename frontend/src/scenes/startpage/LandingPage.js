import React from "react";
import style from "./LandingPage.module.css";
// import "./form.css";
import { useEffect } from "react";
import { useState } from "react";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import app from "../../firebase";
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export default function LandingPage(props) {
  const [loginappear, setloginappear] = useState(false);
  function signIn(e) {
    signInWithPopup(auth, provider)
      .then((result) => {
        // This gives you a Google Access Token. You can use it to access the Google API.
        const credential = GoogleAuthProvider.credentialFromResult(result);
        const token = credential.accessToken;
        // The signed-in user info.
        const user = result.user;
        props.setUser(user);
        props.setLogin(true);
        console.log(user);
        // IdP data available using getAdditionalUserInfo(result)
        // ...
      })
      .catch((error) => {
        // Handle Errors here.
        const errorCode = error.code;
        const errorMessage = error.message;
        // The email of the user's account used.
        const email = error.customData.email;
        // The AuthCredential type that was used.
        const credential = GoogleAuthProvider.credentialFromError(error);
        // ...
      });
  }

  function togglePopup(e) {
    document.getElementById("popupb").disabled = !loginappear;
    setloginappear(!loginappear);
  }
  useEffect(() => {
    if (loginappear == true) {
      let $id = (id) => document.getElementById(id);
      var [login, register, form] = ["login", "register", "form"].map((id) =>
        $id(id)
      );

      [login, register].map((element) => {
        element.onclick = function () {
          [login, register].map(($ele) => {
            $ele.classList.remove("active");
          });
          this.classList.add("active");
          this.getAttribute("id") === "register"
            ? form.classList.add("active")
            : form.classList.remove("active");
        };
      });
    }
  }, [loginappear]);
  return (
    <div className={style.fx}>
      <section className={style.hero}>
        <video className={style.hero_video} autoPlay muted loop>
          <source
            src="https://cdn.zajno.com/dev/codepen/fossil/fossil.mp4"
            type="video/mp4"
          />
        </video>
      </section>
      <div className={style.textholder}>
        <span className={style.h1text}>Stock Market Predictor</span>
        <span className={style.h6text}>Invest to earn Profit</span>
      </div>
      <button id="popupb" className={style.login} onClick={signIn}>
        Login
      </button>
      {loginappear && (
        <section id="form">
          <p id="close-forms" onClick={togglePopup}>
            X
          </p>
          <div id="toggle-forms">
            <button className="waves-effect waves-light active" id="login">
              Login
            </button>
            <button className="waves-effect waves-light" id="register">
              Register
            </button>
          </div>
          <form className="col s12">
            <div className="row center-align">
              <h4 className="white-text">login</h4>
            </div>
            <div className="row">
              <div className="input-field">
                <input id="emailin" type="email" className="validate" />
                <label htmlFor="emailin">Email</label>
              </div>
            </div>
            <div className="row">
              <div className="input-field">
                <input id="passwordin" type="password" className="validate" />
                <label htmlFor="passwordin">Password</label>
              </div>
            </div>
            <div className="row center-align">
              <button className="btn waves-effect waves-light">Login</button>
            </div>
            <p className="forgot">Forgot Password?</p>
            <ul className="animate">
              <li></li>
              <li></li>
              <li></li>
              <li></li>
              <li></li>
              <li></li>
              <li></li>
            </ul>
          </form>
          <form className="col s12">
            <div className="row center-align">
              <h4 className="white-text">register</h4>
            </div>
            <div className="row">
              <div className="input-field">
                <input id="email" type="email" className="validate" />
                <label htmlFor="email">Email</label>
              </div>
            </div>
            <div className="row">
              <div className="input-field">
                <input id="password" type="password" className="validate" />
                <label htmlFor="password">Password</label>
              </div>
            </div>
            <div className="row">
              <div className="input-field">
                <input id="cpassword" type="password" className="validate" />
                <label htmlFor="cpassword">Re-Password</label>
              </div>
            </div>
            <div className="row center-align">
              <button className="btn waves-effect waves-light">Register</button>
            </div>
            <ul className="animate">
              <li></li>
              <li></li>
              <li></li>
              <li></li>
              <li></li>
              <li></li>
              <li></li>
            </ul>
          </form>
        </section>
      )}
    </div>
  );
}
