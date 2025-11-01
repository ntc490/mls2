document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("cmd-form");
  const input = document.getElementById("cmd");
  const output = document.getElementById("terminal-output");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const cmd = input.value.trim();
    if (!cmd) return;

    output.innerHTML += `<div>> ${cmd}</div>`;
    const formData = new FormData();
    formData.append("cmd", cmd);

    const res = await fetch("/command", { method: "POST", body: formData });
    const data = await res.json();
    output.innerHTML += `<div>${data.output}</div>`;
    output.scrollTop = output.scrollHeight;
    input.value = "";
  });
});
