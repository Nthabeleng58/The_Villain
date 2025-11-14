// small helper to show toast messages
function toast(msg) {
    let d = document.createElement('div');
    d.style.position = 'fixed';
    d.style.right = '20px';
    d.style.top = '20px';
    d.style.background = '#111827';
    d.style.color = '#fff';
    d.style.padding = '10px 14px';
    d.style.borderRadius = '6px';
    d.innerText = msg;
    document.body.appendChild(d);
    setTimeout(()=> d.remove(), 3000);
}
