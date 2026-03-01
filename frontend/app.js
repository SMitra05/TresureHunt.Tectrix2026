const API = 'http://localhost:4000';
let participantId = null;
let participantToken = null;
let adminToken = null;
let qrNumber = null;
let currentGroupId = null;

async function call(path, method, body, token) {
  const res = await fetch(API + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

const status = (msg) => (document.getElementById('status').textContent = msg);

registerBtn.onclick = async () => {
  try {
    const data = await call('/auth/participant/register', 'POST', {
      fullName: fullName.value,
      department: department.value,
      collegeEmail: collegeEmail.value,
      collegeRoll: collegeRoll.value,
      year: year.value
    });
    participantId = String(data.participantId);
    participantToken = data.token;
    pid.textContent = participantId;
    status('Registered + logged in: ' + data.participantCode);
  } catch (e) { status(e.message); }
};

loginBtn.onclick = async () => {
  try {
    const data = await call('/auth/participant/login', 'POST', {
      collegeEmail: collegeEmail.value,
      collegeRoll: collegeRoll.value
    });
    participantId = String(data.participantId);
    participantToken = data.token;
    pid.textContent = participantId;
    status('Participant logged in');
  } catch (e) { status(e.message); }
};

logoutBtn.onclick = async () => {
  try {
    if (participantToken) await call('/auth/participant/logout', 'POST', {}, participantToken);
    participantId = null;
    participantToken = null;
    pid.textContent = '-';
    status('Participant logged out');
  } catch (e) { status(e.message); }
};

groupBtn.onclick = async () => {
  try {
    const data = await call('/groups', 'POST', { groupName: groupName.value }, participantToken);
    currentGroupId = data.groupId;
    status('Group created #' + data.groupId);
  } catch (e) { status(e.message); }
};

inviteBtn.onclick = async () => {
  try {
    if (!currentGroupId) throw new Error('Create group first');
    const data = await call(`/groups/${currentGroupId}/invitations`, 'POST', { collegeEmail: inviteEmail.value }, participantToken);
    status('Invitation sent: #' + data.invitationId);
  } catch (e) { status(e.message); }
};

listInvitesBtn.onclick = async () => {
  try {
    const data = await call('/invitations', 'GET', null, participantToken);
    invitesOut.textContent = JSON.stringify(data, null, 2);
    status('Loaded pending invitations');
  } catch (e) { status(e.message); }
};

acceptInviteBtn.onclick = async () => {
  try {
    await call(`/invitations/${inviteId.value}/accept`, 'POST', {}, participantToken);
    status('Invitation accepted');
  } catch (e) { status(e.message); }
};

rejectInviteBtn.onclick = async () => {
  try {
    await call(`/invitations/${inviteId.value}/reject`, 'POST', {}, participantToken);
    status('Invitation rejected');
  } catch (e) { status(e.message); }
};

scanBtn.onclick = async () => {
  try {
    const data = await call('/qr/scan', 'POST', { token: token.value }, participantToken);
    qrNumber = data.qrNumber;
    qrText.textContent = `${data.qrNumber}: ${data.question}`;
    qrArea.classList.remove('hidden');
    status('QR scanned');
  } catch (e) { status(e.message); }
};

submitBtn.onclick = async () => {
  try {
    const data = await call('/submissions', 'POST', {
      qrNumber,
      answer: answer.value,
      explanation: explanation.value
    }, participantToken);
    status(data.message || 'Submission saved');
  } catch (e) { status(e.message); }
};

adminLoginBtn.onclick = async () => {
  try {
    const data = await call('/admin/login', 'POST', { email: adminEmail.value, password: adminPassword.value });
    adminToken = data.token;
    status('Admin logged in');
  } catch (e) { status(e.message); }
};

adminDashboardBtn.onclick = async () => {
  try {
    const data = await call('/admin/dashboard', 'GET', null, adminToken);
    adminOut.textContent = JSON.stringify(data, null, 2);
    status('Dashboard loaded');
  } catch (e) { status(e.message); }
};

gameStateBtn.onclick = async () => {
  try {
    const data = await call('/admin/game/state', 'PATCH', { status: gameStatus.value }, adminToken);
    adminOut.textContent = JSON.stringify(data, null, 2);
    status('Game state updated');
  } catch (e) { status(e.message); }
};

finalQrBtn.onclick = async () => {
  try {
    const data = await call('/admin/game/final-qr', 'PATCH', { qrNumber: finalQr.value }, adminToken);
    adminOut.textContent = JSON.stringify(data, null, 2);
    status('Final QR updated');
  } catch (e) { status(e.message); }
};

broadcastBtn.onclick = async () => {
  try {
    const data = await call('/admin/broadcast', 'POST', { message: broadcast.value }, adminToken);
    adminOut.textContent = JSON.stringify(data, null, 2);
    status('Broadcast updated');
  } catch (e) { status(e.message); }
};
