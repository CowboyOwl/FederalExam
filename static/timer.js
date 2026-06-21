const timer = document.querySelector("#timer");

if (timer) {
  let remaining = Number(timer.dataset.seconds || 0);
  const render = () => {
    const minutes = Math.floor(remaining / 60);
    const seconds = String(remaining % 60).padStart(2, "0");
    timer.textContent = `${minutes}:${seconds}`;
  };
  render();
  const interval = window.setInterval(() => {
    remaining -= 1;
    render();
    if (remaining <= 0) {
      window.clearInterval(interval);
      window.location.reload();
    }
  }, 1000);
}
