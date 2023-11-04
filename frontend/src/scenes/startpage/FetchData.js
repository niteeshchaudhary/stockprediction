import axios from "axios";
import { useEffect, useState } from "react";
import { ThreeCircles } from "react-loader-spinner";
import StockChart from "./StockChart";
import "./mystyle.css";
// const cheerio = require("cheerio");

const codetourl = [
  "tcs",
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
];

// function scrapeChartData(html) {
//   const $ = cheerio.load(html);
//   // Select the element containing the chart data
//   const chartDataElement = $('#highcharts-4rhpq0p-0'); // Replace with the actual selector

//   // Extract the data from the element
//   const chartData = JSON.parse(chartDataElement.text());

//   return chartData;
// }

// async function scraperWeb(symbol, e) {
//   try {
//     console.log(symbol);
//     const response = await axios.get(
//       `http://localhost:5000/api/data/${symbol}`
//     );
//     // const response = await axios.get(
//     //   `http://localhost:5000/api/cprice/${symbol}`
//     // );
//     console.log(response);

//     const $ = cheerio.load(response.data);
//     // const priceElement = $("#quote-header-info").find(
//     //   'fin-streamer[class="Fw(b) Fz(36px) Mb(-4px) D(ib)"]'
//     // );

//     const chrt=scrapeChartData(response.data);
//     console.log(chrt);
//     console.log($("#futuresTab"));
//     const priceElement = $(".ltp");
//     const th = $("#futuresTab").find("th");
//     const td = $("#futuresTab").find("td");
//     const tableTexts = {};
//     th.each((index, wrapperElement) => {
//       const thText = $(wrapperElement).text().trim(); // Trim to remove extra whitespace
//       const tdText = $(td[index]).text().trim();
//       tableTexts[thText] = tdText;
//     });
//     console.log(tableTexts);
//     const price = priceElement.text().trim();
//     const index = price.indexOf(".");
//     const formattedPrice =
//       price.substring(0, index) + "." + price.substring(index + 1, index + 3);
//     return { price: formattedPrice, table: tableTexts };
//   } catch (error) {
//     throw error;
//   }
// }
// scraperWeb(sym, e)
//       .then((data) => {
//         console.log("Stock price:", data);
//         document.getElementById("sub").disabled = false;
//         setcomp(data.table);
//         setprice(data.price);
//       })
//       .catch((error) => {
//         console.error("Error:", error);
//         e.currentTarget.disabled = false;
//       });

async function getData(company) {
  try {
    console.log(company);
    const response = await axios.get(`http://localhost:5000/data/${company}`, {
      headers: {
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
        "Content-Type": "application/json",
      },
    });
    return response;
  } catch (error) {
    throw error;
  }
}

async function fetchCurrent(company) {
  try {
    console.log(company);
    const response = await axios.get(
      `http://localhost:5000/data/current/${company}`,
      {
        headers: {
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
          "Content-Type": "application/json",
        },
      }
    );
    return response;
  } catch (error) {
    throw error;
  }
}
async function fetchPrediction(company) {
  try {
    console.log(company);
    const response = await axios.get(
      `http://localhost:5000/data/predict/${company}`,
      {
        headers: {
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
          "Content-Type": "application/json",
        },
      }
    );
    return response;
  } catch (error) {
    throw error;
  }
}
export default function FetchData() {
  const [prediction, setprediction] = useState(0);
  const [comp, setcomp] = useState([]);
  const [current, setcurrent] = useState([]);
  const [load, setload] = useState(false);
  const [selectedOption, setSelectedOption] = useState("none");
  console.log(current.length);
  const handleSelectChange = (event) => {
    const company = event.target.value;
    console.log(event.target.value);
    if (company === "none") {
      return;
    }
    console.log(event.target.value, "**");
    setSelectedOption(company);
    setprediction(0);
    setload(true);
    getData(company).then((rs) => {
      console.log(rs?.data);
      // setcurrent(rs?.data?.current);
      setcomp(rs?.data);
      setload(false);
    })
    fetchCurrent(company).then((rs) => {
      console.log(rs?.data);
      setcurrent(rs?.data.values);
    });

  };

  const getPrediction = (e) => {
    e.currentTarget.disabled = true;
    setload(true);
    const company = document.getElementById("inp").value;
    fetchPrediction(company).then((rs) => {
      setprediction(rs?.data?.pvalue);
      console.log(rs);
      document.getElementById("sub").disabled = false;
      setload(false);
    });
  };
  useEffect(() => {
    setload(false);
  }, [comp]);

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
            <button onClick={getPrediction} id="sub">
              Predict
            </button>
          </div>
        </div>
        <div className="topright">
          <div className="innertopright">
            {current.length > 0 && <><span className="currentspan"> {current[0]}</span>
            <span
              className="changespan"
              style={{
                color:
                   current[1][0] === "-" ? "red" : "green",
              }}
            >
              {" "}
              {current[1]}
              {current[2]}
            </span></>}
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
      {prediction > 0 && <p>Today's Closing price:{prediction}</p>}
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
