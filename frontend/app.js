const API = 'http://localhost:4000';
let participantId = null;
let qrNumber = null;

async function call(path, method, body) {
  const res = await fetch(API + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(participantId ? { 'x-participant-id': participantId } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

const status = (msg) => document.getElementById('status').textContent = msg;

document.getElementById('registerBtn').onclick = async () => {
  try {
    const data = await call('/auth/participant/register', 'POST', {
      fullName: fullName.value,
      department: department.value,
      collegeEmail: collegeEmail.value,
      collegeRoll: collegeRoll.value,
      year: year.value
    });
    participantId = String(data.participantId);
    document.getElementById('pid').textContent = participantId;
    status('Registered ' + data.participantCode);
  } catch (e) { status(e.message); }
};

document.getElementById('groupBtn').onclick = async () => {
  try {
    const data = await call('/groups', 'POST', { groupName: groupName.value });
    status('Group created #' + data.groupId);
  } catch (e) { status(e.message); }
};

document.getElementById('scanBtn').onclick = async () => {
  try {
    const data = await call('/qr/scan', 'POST', { token: token.value });
    qrNumber = data.qrNumber;
    document.getElementById('qrText').textContent = `${data.qrNumber}: ${data.question}`;
    document.getElementById('qrArea').classList.remove('hidden');
    status('QR scanned');
  } catch (e) { status(e.message); }
};

document.getElementById('submitBtn').onclick = async () => {
  try {
    const data = await call('/submissions', 'POST', {
      qrNumber,
      answer: answer.value,
      explanation: explanation.value
    });
    status(data.message || 'Submission saved');
  } catch (e) { status(e.message); }
};
