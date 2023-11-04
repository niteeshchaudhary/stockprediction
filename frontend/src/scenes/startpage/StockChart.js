import React, { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import Chart from "chart.js/auto";
import "chartjs-adapter-date-fns";

const StockChart = ({ stockData, prediction }) => {
  // const [chartData, setChartData] = useState(null);
  const kp = 10;

  useEffect(() => {
    // Create the new chart
    const ctx = document.getElementById("stockChart");
    var arr = Array(kp).fill(null);
    var data = stockData.map((item) => item.Close).slice(-kp);
    var dates = stockData.map((item) => item.Date).slice(-kp);
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0"); // Month is 0-based, so we add 1 and pad with '0' if needed.
    const day = String(today.getDate()).padStart(2, "0");

    const formattedDate = `${year}-${month}-${day}`;
    console.log(prediction, data[data.length - 1]);
    if (prediction > 0) {
      arr[kp - 1] = data[data.length - 1];
      arr = [...arr, prediction];
      dates = [...dates, formattedDate];
    }
    var newChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: dates,
        datasets: [
          {
            label: "Close Price",
            data: data,
            fill: false,
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1,
          },
          {
            label: "Predicted Close Price",
            data: arr, // Create an array with null values
            pointRadius: 5,
            pointBackgroundColor: "red", // Set the point color to red at the target date index
            borderColor: "rgb(255, 1, 1)",
            tension: 0.1,
          },
        ],
      },
      options: {
        plugins: {
          legend: {
            labels: {
              color: "white", // Change the legend text color
              font: {
                weight: 700,
                size: 14, // Adjust the font size of the legend text
                family: "Arial", // Change the font family of the legend text
              },
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "day",
              displayFormats: {
                day: "yyyy-MM-dd",
              },
            },
            grid: {
              color: "rgba(255, 255, 255, 0.2)", // Change the grid line color
              borderColor: "rgba(255, 255, 255, 0.2)", // Change the border color
              borderWidth: 1, // Adjust the grid line width
            },
            ticks: {
              color: "white", // Change the font color of the ticks
              font: {
                size: 12, // Adjust the font size of the ticks
                family: "Arial", // Change the font family of the ticks
              },
            },
            title: {
              display: true,
              text: "Date",
              font: {
                size: 16, // Adjust the font size as needed
                weight: 800,
                family: "Arial", // Change the font family as needed
                color: "white", // Change the font color
              },
            },
          },
          y: {
            beginAtZero: false,
            grid: {
              color: "rgba(255, 255, 255, 0.2)", // Change the grid line color
              borderColor: "rgba(255, 255, 255, 0.2)", // Change the border color
              borderWidth: 1, // Adjust the grid line width
            },
            ticks: {
              color: "white", // Change the font color of the ticks
              font: {
                size: 12, // Adjust the font size of the ticks
                family: "Arial", // Change the font family of the ticks
              },
            },
            title: {
              display: true,
              text: "Close Price",
              font: {
                size: 18, // Adjust the font size as needed
                weight: 800,
                family: "Arial", // Change the font family as needed
                color: "white", // Change the font color
              },
            },
          },
        },
      },
    });

    // setChartData(newChart);
    return () => {
      newChart.destroy();
    };
  }, [stockData, prediction]);

  return (
    <>
      <h2>Stock Price Chart</h2>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <canvas id="stockChart"></canvas>
      </div>
    </>
  );
};

export default StockChart;
