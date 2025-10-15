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
      return;
    }

    gridContainer.innerHTML = "";
    const grid = Array(height)
      .fill(null)
      .map(() =>
        Array(width)
          .fill(null)
          .map(() => []),
      );

    data.grid.forEach((agent) => {
      if (
        agent.x !== null &&
        agent.y !== null &&
        agent.y < height &&
        agent.x < width
      ) {
        grid[agent.y][agent.x].push(agent);
      }
    });

    if (data.path) {
      data.path.forEach((pos) => {
        if (pos && pos[1] < height && pos[0] < width) {
          const cellData = grid[pos[1]][pos[0]];
          if (!cellData.some((a) => a.type === "survivor")) {
            // Don't draw path over the agent itself
            grid[pos[1]][pos[0]].push({ type: "path" });
          }
        }
      });
    }

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const cell = document.createElement("div");
        cell.classList.add("grid-cell");
        const agentsInCell = grid[y] ? grid[y][x] : [];

        // Find the top-most agent to render
        let agentToRender = null;
        if (agentsInCell.length > 0) {
          agentToRender =
            agentsInCell.find((a) => a.type === "survivor") ||
            agentsInCell.find((a) => a.type === "game_node") ||
            agentsInCell.find((a) => a.type === "obstacle") ||
            agentsInCell.find((a) => a.type === "path");
        }

        if (agentToRender) {
          cell.classList.add(agentToRender.type);
          if (agentToRender.type === "game_node" && agentToRender.active) {
            cell.classList.add("active");
          }
        }
        gridContainer.appendChild(cell);
      }
    }

    daySpan.textContent = data.day;
    stepsTodaySpan.textContent = data.steps_today;
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
      intervalId = setInterval(step, 200); // Faster simulation speed
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
        getInitialState();
      })
      .catch((error) => console.error("Error during reset:", error));
  }

  function getInitialState() {
    fetch("/api/step", { method: "POST" })
      .then((response) => response.json())
      .then((data) => {
        drawGrid(data);
        stopBtn.disabled = true;
        startBtn.disabled = false;
      })
      .catch((error) => console.error("Error fetching initial state:", error));
  }

  startBtn.addEventListener("click", start);
  stopBtn.addEventListener("click", stop);
  resetBtn.addEventListener("click", reset);

  getInitialState();
});
