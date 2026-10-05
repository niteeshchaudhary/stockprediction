import axios from "axios";
import { useEffect, useRef, useState } from "react";
import { ThreeCircles } from "react-loader-spinner";
import StockChart from "./StockChart";
import "./mystyle.css";
// const cheerio = require("cheerio");

const codetourl = [
  // "tata motors",
  "sunpharma",
  "cipla",
  "bajaj finance",
  "ntpc",
  "axis",
  "hdfc",
  "icici",
  "reliance",
  "tata steel",
  // "pgci",
  "sbi",
  // "oangc",
  // "sbilic",
  // "hdfclic",
  // "tatacps",
  "airtel",
  "maruti",
  "coal india",
  "hero",
  // "eicher",
  // "hindalco",
  "infosys",
  "itc",
  "hcl",
  "tcs",
];

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:5000",
  timeout: 60000,
});

const errorMessage = (error) =>
  error.response?.data?.error ||
  "Unable to fetch stock data. Check that the backend is running and try again.";

export default function FetchData() {
  const [prediction, setprediction] = useState({});
  const [comp, setcomp] = useState([]);
  const [current, setcurrent] = useState([]);
  const [load, setload] = useState(false);
  const [selectedOption, setSelectedOption] = useState("none");
  const [error, setError] = useState("");
  const requestId = useRef(0);

  useEffect(() => () => { requestId.current += 1; }, []);

  const handleSelectChange = async (event) => {
    const company = event.target.value;
    const id = ++requestId.current;
    setSelectedOption(company);
    setprediction({});
    setcomp([]);
    setcurrent([]);
    setError("");
    setload(company !== "none");
    if (company === "none") return;

    const symbol = encodeURIComponent(company);
    const results = await Promise.allSettled([
      api.get(`/data/${symbol}`),
      api.get(`/data/current/${symbol}`),
    ]);
    if (id !== requestId.current) return;
    if (results[0].status === "fulfilled") setcomp(results[0].value.data);
    if (results[1].status === "fulfilled") setcurrent(results[1].value.data.values);
    const failures = results.filter((result) => result.status === "rejected");
    setError([...new Set(failures.map((result) => errorMessage(result.reason)))].join(" "));
    setload(false);
  };

  const getPrediction = async () => {
    if (selectedOption === "none" || load || !comp.length) return;
    const id = ++requestId.current;
    setload(true);
    setError("");
    try {
      const response = await api.get(`/data/predict/${encodeURIComponent(selectedOption)}`, {
        timeout: 300000,
      });
      if (id === requestId.current) setprediction(response.data);
    } catch (error) {
      if (id === requestId.current) setError(errorMessage(error));
    } finally {
      if (id === requestId.current) setload(false);
    }
  };

  return (
    <div className="outerdiv">
      <div className="innertop">
        <div className="topleft">
          {load && (
            <ThreeCircles
              height="100"
              width="100"
              color="#4fa94d"
              wrapperStyle={{}}
              wrapperClass=""
              visible={true}
              ariaLabel="three-circles-rotating"
              outerCircleColor=""
              innerCircleColor=""
              middleCircleColor=""
            />
          )}
          <select
            id="inp"
            style={{
              width: "100%",
            }}
            value={selectedOption}
            onChange={handleSelectChange}
          >
            <option value="none">None</option>
            {codetourl.map((e) => (
              <option value={e} key={e}>
                {e}
              </option>
            ))}
          </select>
          <div
            style={{
              display: "flex",
              width: "100%",
              justifyContent: "space-between",
            }}
          >
            <button onClick={getPrediction} id="sub" disabled={load || !comp.length || selectedOption === "none"}>
              Predict
            </button>
          </div>
        </div>
        <div className="topright">
          <div className="innertopright">
            {current.length > 0 && (
              <>
                <span className="currentspan"> {current[0]}</span>
                <span
                  className="changespan"
                  style={{
                    color: current[1][0] === "-" ? "red" : "green",
                  }}
                >
                  {" "}
                  {current[1]}
                  {current[2]}
                </span>
              </>
            )}
          </div>
          <div
            className="topright"
            style={{ width: "35%", minWidth: "3rem" }}
          ></div>
          <div
            className="topright"
            style={{ width: "35%", minWidth: "3rem" }}
          ></div>
        </div>
      </div>
      {prediction?.pvalue > 0 && (
        <p>
          Today's Closing price:{prediction?.pvalue}
          <br />
          Lstm Closing price:{prediction?.pvaluelstm}
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      <StockChart stockData={comp} prediction={prediction} />
      {/* <table border="1">
        <tbody>
          <tr>
            <th>Date</th>
            <th>Open</th>
            <th>Close</th>
            <th>High</th>
            <th>Low</th>
          </tr>
          {comp?.table.slice(-5).map((e, index) => (
            <tr key={index}>
              <td>{e?.Date}</td>
              <td>{e?.Open}</td>
              <td>{e?.Close}</td>
              <td>{e?.High}</td>
              <td>{e?.Low}</td>
            </tr>
          ))}
        </tbody>
      </table> */}
    </div>
  );
}
