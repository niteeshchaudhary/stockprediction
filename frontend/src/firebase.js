// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBvvNyfcHpS6Ahtt-TkccLZgJHLxnVt_0s",
  authDomain: "stocks-227ca.firebaseapp.com",
  databaseURL: "https://stocks-227ca-default-rtdb.firebaseio.com",
  projectId: "stocks-227ca",
  storageBucket: "stocks-227ca.appspot.com",
  messagingSenderId: "683618605196",
  appId: "1:683618605196:web:571ae603d6a619794143a9",
  measurementId: "G-H6CFRX2PHF"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export default app;