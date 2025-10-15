document.addEventListener("DOMContentLoaded", () => {
  const gridContainer = document.getElementById("grid-container");
  const daySpan = document.getElementById("day");
  const stepsTodaySpan = document.getElementById("steps-today");
  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const resetBtn = document.getElementById("reset-btn");

  const width = 10;
  const height = 10;
  let intervalId = null;

  function drawGrid(data) {
    if (!data || !data.grid) {
      console.error("Invalid data received for drawing grid:", data);
      return; // Do not attempt to draw if data is invalid
    }

    gridContainer.innerHTML = "";
    const grid = Array(height)
      .fill(null)
      .map(() => Array(width).fill(null));

    data.grid.forEach((agent) => {
      if (
        agent.x !== null &&
        agent.y !== null &&
        agent.y < height &&
        agent.x < width
      ) {
        grid[agent.y][agent.x] = agent.type;
      }
    });

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const cell = document.createElement("div");
        cell.classList.add("grid-cell");
        const agentType = grid[y] ? grid[y][x] : null;
        if (agentType) {
          cell.classList.add(agentType);
        }
        gridContainer.appendChild(cell);
      }
    }

    // These might not exist in the simplified model, so check first.
    if (daySpan && stepsTodaySpan) {
      daySpan.textContent = data.day || 1;
      stepsTodaySpan.textContent = data.steps_today || 0;
    }
  }

  function step() {
    fetch("/api/step", { method: "POST" })
      .then((response) => response.json())
      .then((data) => {
        drawGrid(data);
      })
      .catch((error) => console.error("Error during step:", error));
  }

  function start() {
    if (intervalId === null) {
      intervalId = setInterval(step, 500); // Speed up simulation for better UX
      startBtn.disabled = true;
      stopBtn.disabled = false;
    }
  }

  function stop() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
      startBtn.disabled = false;
      stopBtn.disabled = true;
    }
  }

  function reset() {
    stop();
    fetch("/api/reset", { method: "POST" })
      .then((response) => response.json())
      .then(() => {
        getInitialState(); // Redraw the initial state after reset
      })
      .catch((error) => console.error("Error during reset:", error));
  }

  function getInitialState() {
    // This endpoint returns the current state without advancing the model
    fetch("/api/step", { method: "POST" })
      .then((response) => response.json())
      .then((data) => {
        drawGrid(data);
        stopBtn.disabled = true;
        startBtn.disabled = false;
      })
      .catch((error) => console.error("Error fetching initial state:", error));
  }

  // Add event listeners
  startBtn.addEventListener("click", start);
  stopBtn.addEventListener("click", stop);
  resetBtn.addEventListener("click", reset);

  // Initial setup
  getInitialState();
});
