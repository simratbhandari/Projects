const f = document.querySelector('#probeForm');
if (f) {
  f.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = document.querySelector('#msg').value || '';
    const res = await fetch(`/echo?msg=${encodeURIComponent(msg)}`);
    const data = await res.json();
    document.querySelector('#probeOut').textContent = JSON.stringify(data, null, 2);
  });
}