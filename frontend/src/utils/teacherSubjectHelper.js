// File Name: teacherSubjectHelper.js
// Description: Utility helper to resolve teacher specialization subject, department, and homeroom role across the frontend.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

export const SUBJECT_MAP = {
  all: { id: 'all', name: 'Tất cả các môn', shortName: 'Tất cả' },
  math: { id: 'math', name: 'Toán học', shortName: 'Toán' },
  physics: { id: 'physics', name: 'Vật lý', shortName: 'Vật lý' },
  chemistry: { id: 'chemistry', name: 'Hóa học', shortName: 'Hóa' },
  literature: { id: 'literature', name: 'Ngữ văn', shortName: 'Văn' },
  english: { id: 'english', name: 'Tiếng Anh', shortName: 'Tiếng Anh' },
  biology: { id: 'biology', name: 'Sinh học', shortName: 'Sinh' },
  history: { id: 'history', name: 'Lịch sử', shortName: 'Sử' },
  informatics: { id: 'informatics', name: 'Tin học', shortName: 'Tin' },
};

/**
 * Resolves teacher subject info based on user profile
 * @param {Object} user - The authenticated user object
 * @returns {{ subjectId: string, subjectName: string, shortName: string }}
 */
export function getTeacherSubjectInfo(user) {
  const name = (user?.full_name || '').toLowerCase();
  const email = (user?.email || '').toLowerCase();
  const phone = (user?.phone || '');

  if (name.includes('long') || email.includes('long') || phone === '0999000006') {
    return { subjectId: 'english', subjectName: 'Tiếng Anh', shortName: 'Tiếng Anh' };
  }
  if (name.includes('an') || email.includes('an') || phone === '0999000004') {
    return { subjectId: 'physics', subjectName: 'Vật lý', shortName: 'Vật lý' };
  }
  if (name.includes('mai') || email.includes('mai') || phone === '0999000005') {
    return { subjectId: 'chemistry', subjectName: 'Hóa học', shortName: 'Hóa' };
  }
  if (name.includes('trang') || email.includes('trang') || phone === '0999000007') {
    return { subjectId: 'literature', subjectName: 'Ngữ văn', shortName: 'Văn' };
  }
  if (name.includes('nguyễn văn a') || email === 'teacher@school.com' || phone === '0999000002') {
    return { subjectId: 'chemistry', subjectName: 'Hóa học', shortName: 'Hóa' };
  }

  return { subjectId: 'math', subjectName: 'Toán học', shortName: 'Toán' };
}

/**
 * Convert Vietnamese subject name to standard subject ID
 * @param {string} name - Subject name (e.g., "Toán học", "Tiếng Anh")
 * @returns {string} Subject ID (e.g., "math", "english")
 */
export function getSubjectIdByName(name) {
  if (!name) return 'math';
  const lower = name.toLowerCase();
  if (lower.includes('anh') || lower.includes('english')) return 'english';
  if (lower.includes('lý') || lower.includes('vật lý') || lower.includes('physics')) return 'physics';
  if (lower.includes('hóa') || lower.includes('chemistry')) return 'chemistry';
  if (lower.includes('văn') || lower.includes('ngữ văn') || lower.includes('literature')) return 'literature';
  if (lower.includes('toán') || lower.includes('math')) return 'math';
  if (lower.includes('sinh') || lower.includes('biology')) return 'biology';
  if (lower.includes('sử') || lower.includes('lịch sử') || lower.includes('history')) return 'history';
  if (lower.includes('tin') || lower.includes('informatics')) return 'informatics';
  return 'math';
}

/**
 * Get detailed profile defaults matching the specific teacher account
 * @param {Object} user - The authenticated user object
 * @returns {Object} Full profile defaults
 */
export function getTeacherProfileDefaults(user) {
  const name = (user?.full_name || '').toLowerCase();
  const email = (user?.email || '').toLowerCase();
  const phone = (user?.phone || '');

  // Thầy Lê Hoàng Long - GV Bộ môn Tiếng Anh (không chủ nhiệm)
  if (name.includes('long') || email.includes('long') || phone === '0999000006') {
    return {
      department: 'Tổ Ngoại ngữ',
      position: 'Giáo viên bộ môn Tiếng Anh',
      degree: 'Thạc sĩ Ngôn ngữ Anh',
      isHomeroom: false,
      homeroomClass: null,
      teacherCode: 'GV-2023-089'
    };
  }

  // Thầy Nguyễn Văn An - GV Bộ môn Vật lý (Chủ nhiệm 11B2)
  if (name.includes('an') || email.includes('an') || phone === '0999000004') {
    return {
      department: 'Tổ Vật lý - Công nghệ',
      position: 'Giáo viên bộ môn Vật lý • Chủ nhiệm 11B2',
      degree: 'Thạc sĩ Sư phạm Vật lý',
      isHomeroom: true,
      homeroomClass: '11B2',
      teacherCode: 'GV-2023-042'
    };
  }

  // Cô Trần Thị Mai - GV Bộ môn Hóa học (Chủ nhiệm 10A3)
  if (name.includes('mai') || email.includes('mai') || phone === '0999000005') {
    return {
      department: 'Tổ Hóa học - Sinh học',
      position: 'Giáo viên bộ môn Hóa học • Chủ nhiệm 10A3',
      degree: 'Thạc sĩ Sư phạm Hóa học',
      isHomeroom: true,
      homeroomClass: '10A3',
      teacherCode: 'GV-2023-055'
    };
  }

  // Cô Phạm Thu Trang - GV Bộ môn Ngữ văn (không chủ nhiệm)
  if (name.includes('trang') || email.includes('trang') || phone === '0999000007') {
    return {
      department: 'Tổ Ngữ văn',
      position: 'Giáo viên bộ môn Ngữ văn',
      degree: 'Cử nhân Sư phạm Ngữ văn',
      isHomeroom: false,
      homeroomClass: null,
      teacherCode: 'GV-2023-078'
    };
  }

  // Sample Teacher (Thầy Nguyễn Văn A) - GV Bộ môn Hóa / Chủ nhiệm 12A1
  if (name.includes('nguyễn văn a') || email === 'teacher@school.com' || phone === '0999000002') {
    return {
      department: 'Tổ Hóa học - Sinh học',
      position: 'Giáo viên bộ môn Hóa học • Chủ nhiệm 12A1',
      degree: 'Thạc sĩ Sư phạm Hóa học',
      isHomeroom: true,
      homeroomClass: '12A1',
      teacherCode: 'GV-2023-012'
    };
  }

  return {
    department: 'Tổ Toán - Tin học',
    position: 'Giáo viên bộ môn Toán',
    degree: 'Cử nhân Sư phạm Toán học',
    isHomeroom: false,
    homeroomClass: null,
    teacherCode: 'GV-2023-001'
  };
}
