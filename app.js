const CLASSES = ['6', '7', '8', '9', '10', '11', '12'];
const SECTIONS = ['A', 'B', 'C', 'D'];
const PERIODS = ['1', '2', '3', '4', '5', '6', '7', '8'];

const DB_KEYS = {
  students: 'attendance_students',
  records: 'attendance_records'
};

function getStudents() {
  const data = localStorage.getItem(DB_KEYS.students);
  return data ? JSON.parse(data) : [];
}

function saveStudents(students) {
  localStorage.setItem(DB_KEYS.students, JSON.stringify(students));
}

function getRecords() {
  const data = localStorage.getItem(DB_KEYS.records);
  return data ? JSON.parse(data) : {};
}

function saveRecords(records) {
  localStorage.setItem(DB_KEYS.records, JSON.stringify(records));
}

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function populateClassSelects() {
  const selects = ['roster-class', 'student-class', 'att-class', 'report-class'];
  selects.forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    const firstOption = select.querySelector('option');
    select.innerHTML = '';
    select.appendChild(firstOption);
    CLASSES.forEach(cls => {
      const option = document.createElement('option');
      option.value = cls;
      option.textContent = `Class ${cls}`;
      select.appendChild(option);
    });
  });
}

function setupTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
    });
  });
}

function setupRoster() {
  document.getElementById('view-roster-btn').addEventListener('click', viewRoster);
  document.getElementById('add-student-btn').addEventListener('click', addStudent);

  document.getElementById('roster-class').addEventListener('change', () => {
    if (document.getElementById('roster-class').value && document.getElementById('roster-section').value) {
      viewRoster();
    }
  });

  document.getElementById('roster-section').addEventListener('change', () => {
    if (document.getElementById('roster-class').value && document.getElementById('roster-section').value) {
      viewRoster();
    }
  });
}

function viewRoster() {
  const cls = document.getElementById('roster-class').value;
  const section = document.getElementById('roster-section').value;

  if (!cls || !section) {
    showToast('Please select both class and section', 'error');
    return;
  }

  const students = getStudents().filter(s => s.class === cls && s.section === section);
  const tbody = document.getElementById('roster-body');
  const empty = document.getElementById('roster-empty');
  const table = document.getElementById('roster-table');
  const title = document.getElementById('roster-title');

  title.textContent = `Class ${cls} - Section ${section} (${students.length} students)`;

  if (students.length === 0) {
    table.style.display = 'none';
    empty.style.display = 'block';
    return;
  }

  table.style.display = 'table';
  empty.style.display = 'none';

  students.sort((a, b) => a.roll - b.roll);

  tbody.innerHTML = students.map(student => `
    <tr data-id="${student.id}">
      <td>${student.roll}</td>
      <td>${student.name}</td>
      <td>${student.class}</td>
      <td>${student.section}</td>
      <td>
        <button class="action-btn remove-btn" onclick="removeStudent('${student.id}')">Remove</button>
      </td>
    </tr>
  `).join('');
}

function addStudent() {
  const name = document.getElementById('student-name').value.trim();
  const roll = document.getElementById('student-roll').value;
  const cls = document.getElementById('student-class').value;
  const section = document.getElementById('student-section').value;

  if (!name || !roll || !cls || !section) {
    showToast('Please fill all fields', 'error');
    return;
  }

  const students = getStudents();
  const duplicate = students.find(s =>
    s.class === cls && s.section === section && (s.roll === parseInt(roll) || s.name.toLowerCase() === name.toLowerCase())
  );

  if (duplicate) {
    showToast('Student with same roll number or name already exists in this class/section', 'error');
    return;
  }

  students.push({
    id: generateId(),
    name,
    roll: parseInt(roll),
    class: cls,
    section,
    createdAt: new Date().toISOString()
  });

  saveStudents(students);
  showToast(`Student "${name}" added successfully`);

  document.getElementById('student-name').value = '';
  document.getElementById('student-roll').value = '';
  document.getElementById('student-class').value = '';
  document.getElementById('student-section').value = '';
}

function removeStudent(id) {
  if (!confirm('Are you sure you want to remove this student?')) return;

  let students = getStudents();
  const student = students.find(s => s.id === id);
  students = students.filter(s => s.id !== id);
  saveStudents(students);

  showToast(`Student "${student?.name}" removed`);

  const cls = document.getElementById('roster-class').value;
  const section = document.getElementById('roster-section').value;
  if (cls && section) viewRoster();
}

function setupAttendance() {
  document.getElementById('att-date').valueAsDate = new Date();
  document.getElementById('load-attendance-btn').addEventListener('click', loadAttendance);
  document.getElementById('mark-all-present').addEventListener('click', () => markAll('Present'));
  document.getElementById('mark-all-absent').addEventListener('click', () => markAll('Absent'));
  document.getElementById('save-attendance-btn').addEventListener('click', saveAttendance);
}

function loadAttendance() {
  const date = document.getElementById('att-date').value;
  const cls = document.getElementById('att-class').value;
  const section = document.getElementById('att-section').value;
  const period = document.getElementById('att-period').value;

  if (!date || !cls || !section || !period) {
    showToast('Please select date, class, section, and period', 'error');
    return;
  }

  const students = getStudents().filter(s => s.class === cls && s.section === section);
  const records = getRecords();
  const recordKey = `${date}_${cls}_${section}_${period}`;
  const existingRecord = records[recordKey];

  const tbody = document.getElementById('attendance-body');
  const empty = document.getElementById('attendance-empty');
  const table = document.getElementById('attendance-table');
  const title = document.getElementById('attendance-title');

  title.textContent = `Class ${cls} - Section ${section} | Period ${period} | ${new Date(date).toLocaleDateString()}`;

  if (students.length === 0) {
    table.style.display = 'none';
    empty.style.display = 'block';
    return;
  }

  table.style.display = 'table';
  empty.style.display = 'none';

  students.sort((a, b) => a.roll - b.roll);

  tbody.innerHTML = students.map(student => {
    const status = existingRecord?.[student.id] || '';
    return `
      <tr data-id="${student.id}">
        <td>${student.roll}</td>
        <td>${student.name}</td>
        <td>
          <select class="status-select ${status ? 'status-' + status.toLowerCase() : ''}" data-student="${student.id}">
            <option value="">Select</option>
            <option value="Present" ${status === 'Present' ? 'selected' : ''}>Present</option>
            <option value="Absent" ${status === 'Absent' ? 'selected' : ''}>Absent</option>
            <option value="Late" ${status === 'Late' ? 'selected' : ''}>Late</option>
          </select>
        </td>
      </tr>
    `;
  }).join('');

  document.querySelectorAll('.status-select').forEach(select => {
    select.addEventListener('change', function() {
      this.className = 'status-select';
      if (this.value) this.classList.add('status-' + this.value.toLowerCase());
    });
  });
}

function markAll(status) {
  document.querySelectorAll('.status-select').forEach(select => {
    select.value = status;
    select.className = 'status-select status-' + status.toLowerCase();
  });
}

function saveAttendance() {
  const date = document.getElementById('att-date').value;
  const cls = document.getElementById('att-class').value;
  const section = document.getElementById('att-section').value;
  const period = document.getElementById('att-period').value;
  const recordKey = `${date}_${cls}_${section}_${period}`;

  const records = getRecords();
  const selectElements = document.querySelectorAll('.status-select');
  let hasSelection = false;

  selectElements.forEach(select => {
    if (select.value) hasSelection = true;
  });

  if (!hasSelection) {
    showToast('Please mark at least one student', 'error');
    return;
  }

  records[recordKey] = {};
  selectElements.forEach(select => {
    records[recordKey][select.dataset.student] = select.value || 'Absent';
  });

  saveRecords(records);
  showToast('Attendance saved successfully');
}

function setupReports() {
  const today = new Date();
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(today.getDate() - 30);

  document.getElementById('report-to').valueAsDate = today;
  document.getElementById('report-from').valueAsDate = thirtyDaysAgo;

  document.getElementById('generate-report-btn').addEventListener('click', generateReport);
}

function generateReport() {
  const cls = document.getElementById('report-class').value;
  const section = document.getElementById('report-section').value;
  const period = document.getElementById('report-period').value;
  const fromDate = document.getElementById('report-from').value;
  const toDate = document.getElementById('report-to').value;

  if (!cls || !section || !fromDate || !toDate) {
    showToast('Please select class, section, and date range', 'error');
    return;
  }

  const students = getStudents().filter(s => s.class === cls && s.section === section);
  const records = getRecords();

  const studentStats = students.map(student => {
    let present = 0;
    let absent = 0;
    let late = 0;
    let total = 0;

    Object.keys(records).forEach(key => {
      const [date, recClass, recSection, recPeriod] = key.split('_');

      if (recClass !== cls || recSection !== section) return;
      if (period && recPeriod !== period) return;
      if (date < fromDate || date > toDate) return;

      const status = records[key][student.id];
      if (status) {
        total++;
        if (status === 'Present') present++;
        else if (status === 'Absent') absent++;
        else if (status === 'Late') {
          late++;
          present++;
        }
      }
    });

    const percentage = total > 0 ? Math.round((present / total) * 100) : 0;

    return {
      ...student,
      present,
      absent,
      late,
      total,
      percentage
    };
  });

  const tbody = document.getElementById('report-body');
  const empty = document.getElementById('report-empty');
  const table = document.getElementById('report-table');
  const title = document.getElementById('report-title');
  const summary = document.getElementById('report-summary');

  const periodLabel = period ? `Period ${period}` : 'All Periods';
  title.textContent = `Class ${cls} - Section ${section} | ${periodLabel} | ${new Date(fromDate).toLocaleDateString()} - ${new Date(toDate).toLocaleDateString()}`;

  if (students.length === 0) {
    table.style.display = 'none';
    summary.style.display = 'none';
    empty.style.display = 'block';
    return;
  }

  table.style.display = 'table';
  summary.style.display = 'grid';
  empty.style.display = 'none';

  const totalPresent = studentStats.reduce((sum, s) => sum + s.present, 0);
  const totalAbsent = studentStats.reduce((sum, s) => sum + s.absent, 0);
  const totalDays = studentStats.reduce((sum, s) => sum + s.total, 0);
  const avgPercentage = studentStats.length > 0
    ? Math.round(studentStats.reduce((sum, s) => sum + s.percentage, 0) / studentStats.length)
    : 0;

  summary.innerHTML = `
    <div class="summary-card">
      <div class="value">${studentStats.length}</div>
      <div class="label">Total Students</div>
    </div>
    <div class="summary-card">
      <div class="value">${totalDays}</div>
      <div class="label">Total Records</div>
    </div>
    <div class="summary-card">
      <div class="value">${avgPercentage}%</div>
      <div class="label">Avg Attendance</div>
    </div>
    <div class="summary-card">
      <div class="value">${totalPresent}</div>
      <div class="label">Total Present</div>
    </div>
    <div class="summary-card">
      <div class="value">${totalAbsent}</div>
      <div class="label">Total Absent</div>
    </div>
  `;

  studentStats.sort((a, b) => a.roll - b.roll);

  tbody.innerHTML = studentStats.map(student => {
    let fillClass = 'fill-high';
    if (student.percentage < 75) fillClass = 'fill-low';
    else if (student.percentage < 90) fillClass = 'fill-medium';

    return `
      <tr>
        <td>${student.roll}</td>
        <td>${student.name}</td>
        <td>${student.present}</td>
        <td>${student.absent}</td>
        <td>
          ${student.total > 0 ? student.percentage + '%' : 'N/A'}
          <div class="percentage-bar">
            <div class="percentage-fill ${fillClass}" style="width: ${student.total > 0 ? student.percentage : 0}%"></div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  populateClassSelects();
  setupTabs();
  setupRoster();
  setupAttendance();
  setupReports();
});
