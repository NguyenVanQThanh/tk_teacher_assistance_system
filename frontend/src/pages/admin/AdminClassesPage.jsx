// File Name: AdminClassesPage.jsx
// Description: Comprehensive School & Class Management screen for Admin portal with capacity indicators and teacher assignment.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  GraduationCap, 
  Download, 
  Plus, 
  Search, 
  X, 
  RotateCw, 
  ChevronDown, 
  Eye, 
  Edit2, 
  MoreVertical, 
  UserPlus, 
  AlertTriangle, 
  CheckCircle2, 
  ChevronLeft, 
  ChevronRight, 
  Wand2, 
  FileSpreadsheet, 
  Calendar,
  AlertCircle,
  LayoutGrid,
  Users,
  Star,
  PieChart,
  ArrowUpDown,
  Printer,
  UserCheck,
  Building2,
  Upload,
  Info,
  FileText
} from 'lucide-react';
import './AdminClassesPage.css';

export default function AdminClassesPage() {
  // State for tabs & filters
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'k10' | 'k11' | 'k12'
  const [searchQuery, setSearchQuery] = useState('');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [teacherStatusFilter, setTeacherStatusFilter] = useState('all');
  const [selectedIds, setSelectedIds] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Active filter tags state
  const [filterTags, setFilterTags] = useState([
    { id: 'grade', label: 'Tất cả khối lớp (64)' },
    { id: 'year', label: 'Niên khóa: 2024 - 2025' }
  ]);

  // Modals state
  const [selectedClass, setSelectedClass] = useState(null);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Helper for sorting Vietnamese names alphabetically by given name (Tên), then middle/family names (Họ và tên đệm)
  const compareVietnameseNames = (aName, bName) => {
    const getParts = (name) => {
      const trimmed = (name || '').trim();
      const lastSpace = trimmed.lastIndexOf(' ');
      if (lastSpace === -1) {
        return { firstName: trimmed, lastName: '' };
      }
      return {
        firstName: trimmed.slice(lastSpace + 1),
        lastName: trimmed.slice(0, lastSpace).trim()
      };
    };

    const aParts = getParts(aName);
    const bParts = getParts(bName);

    const compFirst = aParts.firstName.localeCompare(bParts.firstName, 'vi', { sensitivity: 'base' });
    if (compFirst !== 0) return compFirst;

    return aParts.lastName.localeCompare(bParts.lastName, 'vi', { sensitivity: 'base' });
  };

  // Students list for class detail dialog matching mockup (45 students)
  const defaultClassStudents = [
    {
      id: 'HS2024101',
      code: 'HS2024101',
      name: 'Nguyễn Hoàng Nam',
      email: 'hoangnam.12a1@academic.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=120',
      birthDate: '14/02/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Văn Dũng',
      parentRole: 'Bố',
      parentPhone: '0983.112.445',
      gpa: 9.4,
      rank: 'Xuất sắc',
      role: 'Lớp trưởng',
      starred: false
    },
    {
      id: 'HS2024102',
      code: 'HS2024102',
      name: 'Trần Thùy Chi',
      email: 'thuychi.12a1@academic.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=120',
      birthDate: '28/05/2007',
      gender: 'Nữ',
      parentName: 'Phạm Thanh Hương',
      parentRole: 'Mẹ',
      parentPhone: '0912.889.332',
      gpa: 9.2,
      rank: 'Xuất sắc',
      role: 'Bí thư',
      starred: true
    },
    {
      id: 'HS2024103',
      code: 'HS2024103',
      name: 'Lê Quang Huy',
      email: 'quanghuy.12a1@academic.edu.vn',
      avatarText: 'LQ',
      avatarBg: '#E0F2FE',
      avatarColor: '#0284C7',
      birthDate: '10/09/2007',
      gender: 'Nam',
      parentName: 'Lê Văn Thành',
      parentRole: 'Bố',
      parentPhone: '0904.556.778',
      gpa: 9.1,
      rank: 'Giỏi',
      role: 'Tổ trưởng',
      starred: false
    },
    {
      id: 'HS2024104',
      code: 'HS2024104',
      name: 'Phạm Phương Anh',
      email: 'phuonganh.12a1@academic.edu.vn',
      avatarText: 'PA',
      avatarBg: '#F3E8FF',
      avatarColor: '#7E22CE',
      birthDate: '05/11/2007',
      gender: 'Nữ',
      parentName: 'Vũ Thị Nga',
      parentRole: 'Mẹ',
      parentPhone: '0978.223.119',
      gpa: 8.9,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024105',
      code: 'HS2024105',
      name: 'Đặng Gia Bảo',
      email: 'giabao.12a1@academic.edu.vn',
      avatarText: 'ĐB',
      avatarBg: '#DCFCE7',
      avatarColor: '#15803D',
      birthDate: '22/01/2007',
      gender: 'Nam',
      parentName: 'Đặng Văn Hùng',
      parentRole: 'Bố',
      parentPhone: '0936.445.889',
      gpa: 8.8,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024106',
      code: 'HS2024106',
      name: 'Vũ Thảo My',
      email: 'thaomy.12a1@academic.edu.vn',
      avatarText: 'VM',
      avatarBg: '#FCE7F3',
      avatarColor: '#BE185D',
      birthDate: '18/08/2007',
      gender: 'Nữ',
      parentName: 'Hoàng Bích Thủy',
      parentRole: 'Mẹ',
      parentPhone: '0945.667.123',
      gpa: 8.7,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024107',
      code: 'HS2024107',
      name: 'Bùi Đức Trọng',
      email: 'ductrong.12a1@academic.edu.vn',
      avatarText: 'BT',
      avatarBg: '#FAE8FF',
      avatarColor: '#A21CAF',
      birthDate: '30/03/2007',
      gender: 'Nam',
      parentName: 'Bùi Quang Minh',
      parentRole: 'Bố',
      parentPhone: '0962.334.551',
      gpa: 8.5,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024108',
      code: 'HS2024108',
      name: 'Hoàng Khánh Linh',
      email: 'khanhlinh.12a1@academic.edu.vn',
      avatarText: 'HL',
      avatarBg: '#E0E7FF',
      avatarColor: '#4338CA',
      birthDate: '12/12/2007',
      gender: 'Nữ',
      parentName: 'Nguyễn Thị Mai',
      parentRole: 'Mẹ',
      parentPhone: '0918.775.443',
      gpa: 8.3,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024109',
      code: 'HS2024109',
      name: 'Nguyễn Tuấn Anh',
      email: 'tuananh.12a1@academic.edu.vn',
      avatarText: 'TA',
      avatarBg: '#FEF3C7',
      avatarColor: '#B45309',
      birthDate: '03/04/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Trọng Tấn',
      parentRole: 'Bố',
      parentPhone: '0903.111.222',
      gpa: 9.3,
      rank: 'Xuất sắc',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024110',
      code: 'HS2024110',
      name: 'Bùi Hoàng Việt Anh',
      email: 'vietanh.12a1@academic.edu.vn',
      avatarText: 'VA',
      avatarBg: '#EDE9FE',
      avatarColor: '#6D28D9',
      birthDate: '15/06/2007',
      gender: 'Nam',
      parentName: 'Bùi Văn Hoàng',
      parentRole: 'Bố',
      parentPhone: '0912.334.455',
      gpa: 8.6,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024111',
      code: 'HS2024111',
      name: 'Dương Ngọc Ánh',
      email: 'ngocanh.12a1@academic.edu.vn',
      avatarText: 'NA',
      avatarBg: '#FCE7F3',
      avatarColor: '#9D174D',
      birthDate: '24/09/2007',
      gender: 'Nữ',
      parentName: 'Dương Đình Nghệ',
      parentRole: 'Bố',
      parentPhone: '0988.776.655',
      gpa: 9.0,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024112',
      code: 'HS2024112',
      name: 'Nguyễn Thanh Bình',
      email: 'thanhbinh.12a1@academic.edu.vn',
      avatarText: 'TB',
      avatarBg: '#DCFCE7',
      avatarColor: '#166534',
      birthDate: '11/01/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Văn Bình',
      parentRole: 'Bố',
      parentPhone: '0977.888.999',
      gpa: 8.4,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024113',
      code: 'HS2024113',
      name: 'Hà Đức Chinh',
      email: 'ducchinh.12a1@academic.edu.vn',
      avatarText: 'DC',
      avatarBg: '#FFEDD5',
      avatarColor: '#C2410C',
      birthDate: '20/07/2007',
      gender: 'Nam',
      parentName: 'Hà Văn Sang',
      parentRole: 'Bố',
      parentPhone: '0934.567.890',
      gpa: 8.2,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024114',
      code: 'HS2024114',
      name: 'Lâm Quốc Cường',
      email: 'quoccuong.12a1@academic.edu.vn',
      avatarText: 'QC',
      avatarBg: '#E0F2FE',
      avatarColor: '#0369A1',
      birthDate: '09/02/2007',
      gender: 'Nam',
      parentName: 'Lâm Văn Thảo',
      parentRole: 'Bố',
      parentPhone: '0943.210.987',
      gpa: 8.7,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024115',
      code: 'HS2024115',
      name: 'Bùi Tiến Dũng',
      email: 'tiendung.12a1@academic.edu.vn',
      avatarText: 'TD',
      avatarBg: '#E0E7FF',
      avatarColor: '#3730A3',
      birthDate: '28/02/2007',
      gender: 'Nam',
      parentName: 'Bùi Văn Khánh',
      parentRole: 'Bố',
      parentPhone: '0981.234.567',
      gpa: 9.1,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024116',
      code: 'HS2024116',
      name: 'Nhâm Mạnh Dũng',
      email: 'manhdung.12a1@academic.edu.vn',
      avatarText: 'MD',
      avatarBg: '#F3E8FF',
      avatarColor: '#6B21A8',
      birthDate: '12/04/2007',
      gender: 'Nam',
      parentName: 'Nhâm Văn Toản',
      parentRole: 'Bố',
      parentPhone: '0972.345.678',
      gpa: 8.6,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024117',
      code: 'HS2024117',
      name: 'Nguyễn Anh Dũng',
      email: 'anhdung.12a1@academic.edu.vn',
      avatarText: 'AD',
      avatarBg: '#DCFCE7',
      avatarColor: '#15803D',
      birthDate: '19/08/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Văn Thái',
      parentRole: 'Bố',
      parentPhone: '0963.456.789',
      gpa: 8.5,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024118',
      code: 'HS2024118',
      name: 'Nguyễn Phong Hồng Duy',
      email: 'hongduy.12a1@academic.edu.vn',
      avatarText: 'HD',
      avatarBg: '#FEF3C7',
      avatarColor: '#92400E',
      birthDate: '13/06/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Hồng Sơn',
      parentRole: 'Bố',
      parentPhone: '0915.678.901',
      gpa: 8.8,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024119',
      code: 'HS2024119',
      name: 'Ngô Thành Đạt',
      email: 'thanhdat.12a1@academic.edu.vn',
      avatarText: 'TĐ',
      avatarBg: '#FEE2E2',
      avatarColor: '#B91C1C',
      birthDate: '01/10/2007',
      gender: 'Nam',
      parentName: 'Ngô Văn Cường',
      parentRole: 'Bố',
      parentPhone: '0908.112.233',
      gpa: 8.9,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024120',
      code: 'HS2024120',
      name: 'Lê Văn Đức',
      email: 'vanduc.12a1@academic.edu.vn',
      avatarText: 'VĐ',
      avatarBg: '#E0F2FE',
      avatarColor: '#075985',
      birthDate: '17/03/2007',
      gender: 'Nam',
      parentName: 'Lê Văn Trọng',
      parentRole: 'Bố',
      parentPhone: '0937.223.344',
      gpa: 8.6,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024121',
      code: 'HS2024121',
      name: 'Phan Văn Đức',
      email: 'phanvanduc.12a1@academic.edu.vn',
      avatarText: 'PĐ',
      avatarBg: '#EDE9FE',
      avatarColor: '#5B21B6',
      birthDate: '11/04/2007',
      gender: 'Nam',
      parentName: 'Phan Văn Dần',
      parentRole: 'Bố',
      parentPhone: '0948.334.455',
      gpa: 9.3,
      rank: 'Xuất sắc',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024122',
      code: 'HS2024122',
      name: 'Nguyễn Quang Hải',
      email: 'quanghai.12a1@academic.edu.vn',
      avatarText: 'QH',
      avatarBg: '#FEF3C7',
      avatarColor: '#B45309',
      birthDate: '12/04/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Quang Thuần',
      parentRole: 'Bố',
      parentPhone: '0919.445.566',
      gpa: 9.5,
      rank: 'Xuất sắc',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024123',
      code: 'HS2024123',
      name: 'Phạm Tuấn Hải',
      email: 'tuanhai.12a1@academic.edu.vn',
      avatarText: 'TH',
      avatarBg: '#DCFCE7',
      avatarColor: '#14532D',
      birthDate: '19/05/2007',
      gender: 'Nam',
      parentName: 'Phạm Văn Hùng',
      parentRole: 'Bố',
      parentPhone: '0982.556.677',
      gpa: 8.8,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024124',
      code: 'HS2024124',
      name: 'Phạm Thúy Hằng',
      email: 'thuyhang.12a1@academic.edu.vn',
      avatarText: 'TH',
      avatarBg: '#FCE7F3',
      avatarColor: '#831843',
      birthDate: '07/07/2007',
      gender: 'Nữ',
      parentName: 'Trịnh Thị Lan',
      parentRole: 'Mẹ',
      parentPhone: '0973.667.788',
      gpa: 8.4,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024125',
      code: 'HS2024125',
      name: 'Đoàn Văn Hậu',
      email: 'vanhau.12a1@academic.edu.vn',
      avatarText: 'VH',
      avatarBg: '#E0E7FF',
      avatarColor: '#312E81',
      birthDate: '19/04/2007',
      gender: 'Nam',
      parentName: 'Đoàn Quốc Thắng',
      parentRole: 'Bố',
      parentPhone: '0964.778.899',
      gpa: 8.7,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024126',
      code: 'HS2024126',
      name: 'Phan Gia Huy',
      email: 'giahuy.12a1@academic.edu.vn',
      avatarText: 'GH',
      avatarBg: '#E0F2FE',
      avatarColor: '#0C4A6E',
      birthDate: '23/11/2007',
      gender: 'Nam',
      parentName: 'Phan Đình Giáp',
      parentRole: 'Bố',
      parentPhone: '0905.889.900',
      gpa: 8.3,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024127',
      code: 'HS2024127',
      name: 'Chu Quang Khải',
      email: 'quangkhai.12a1@academic.edu.vn',
      avatarText: 'QK',
      avatarBg: '#F3E8FF',
      avatarColor: '#581C87',
      birthDate: '30/08/2007',
      gender: 'Nam',
      parentName: 'Chu Văn Quý',
      parentRole: 'Bố',
      parentPhone: '0916.990.011',
      gpa: 8.5,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024128',
      code: 'HS2024128',
      name: 'Khuất Văn Khang',
      email: 'vankhang.12a1@academic.edu.vn',
      avatarText: 'VK',
      avatarBg: '#DCFCE7',
      avatarColor: '#166534',
      birthDate: '11/05/2007',
      gender: 'Nam',
      parentName: 'Khuất Duy Tiến',
      parentRole: 'Bố',
      parentPhone: '0927.001.122',
      gpa: 9.0,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024129',
      code: 'HS2024129',
      name: 'Đặng Văn Lâm',
      email: 'vanlam.12a1@academic.edu.vn',
      avatarText: 'VL',
      avatarBg: '#E0F2FE',
      avatarColor: '#0284C7',
      birthDate: '13/08/2007',
      gender: 'Nam',
      parentName: 'Đặng Văn Sơn',
      parentRole: 'Bố',
      parentPhone: '0938.112.233',
      gpa: 9.2,
      rank: 'Xuất sắc',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024130',
      code: 'HS2024130',
      name: 'Đỗ Duy Mạnh',
      email: 'duymanh.12a1@academic.edu.vn',
      avatarText: 'DM',
      avatarBg: '#EDE9FE',
      avatarColor: '#6D28D9',
      birthDate: '29/09/2007',
      gender: 'Nam',
      parentName: 'Đỗ Nguyên Hải',
      parentRole: 'Bố',
      parentPhone: '0949.223.344',
      gpa: 8.7,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024131',
      code: 'HS2024131',
      name: 'Trần Nguyên Mạnh',
      email: 'nguyenmanh.12a1@academic.edu.vn',
      avatarText: 'NM',
      avatarBg: '#FEF3C7',
      avatarColor: '#B45309',
      birthDate: '20/12/2007',
      gender: 'Nam',
      parentName: 'Trần Văn Cảnh',
      parentRole: 'Bố',
      parentPhone: '0981.334.455',
      gpa: 8.4,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024132',
      code: 'HS2024132',
      name: 'Dụng Quang Nho',
      email: 'quangnho.12a1@academic.edu.vn',
      avatarText: 'QN',
      avatarBg: '#DCFCE7',
      avatarColor: '#15803D',
      birthDate: '01/01/2007',
      gender: 'Nam',
      parentName: 'Dụng Văn Nam',
      parentRole: 'Bố',
      parentPhone: '0972.445.566',
      gpa: 8.2,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024133',
      code: 'HS2024133',
      name: 'Đỗ Thị Kim Oanh',
      email: 'kimoanh.12a1@academic.edu.vn',
      avatarText: 'KO',
      avatarBg: '#FCE7F3',
      avatarColor: '#BE185D',
      birthDate: '16/03/2007',
      gender: 'Nữ',
      parentName: 'Nguyễn Thị Lụa',
      parentRole: 'Mẹ',
      parentPhone: '0963.556.677',
      gpa: 8.6,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024134',
      code: 'HS2024134',
      name: 'Nguyễn Công Phượng',
      email: 'congphuong.12a1@academic.edu.vn',
      avatarText: 'CP',
      avatarBg: '#FFEDD5',
      avatarColor: '#C2410C',
      birthDate: '21/01/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Công Bảy',
      parentRole: 'Bố',
      parentPhone: '0914.667.788',
      gpa: 8.9,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024135',
      code: 'HS2024135',
      name: 'Đinh Bích Phương',
      email: 'bichphuong.12a1@academic.edu.vn',
      avatarText: 'BP',
      avatarBg: '#F3E8FF',
      avatarColor: '#7E22CE',
      birthDate: '10/10/2007',
      gender: 'Nữ',
      parentName: 'Đinh Tiến Đạt',
      parentRole: 'Bố',
      parentPhone: '0925.778.899',
      gpa: 9.3,
      rank: 'Xuất sắc',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024136',
      code: 'HS2024136',
      name: 'Hồ Minh Quân',
      email: 'minhquan.12a1@academic.edu.vn',
      avatarText: 'MQ',
      avatarBg: '#E0F2FE',
      avatarColor: '#0284C7',
      birthDate: '05/09/2007',
      gender: 'Nam',
      parentName: 'Hồ Văn Trung',
      parentRole: 'Bố',
      parentPhone: '0936.889.900',
      gpa: 8.8,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024137',
      code: 'HS2024137',
      name: 'Mai Xuân Quyết',
      email: 'xuanquyet.12a1@academic.edu.vn',
      avatarText: 'XQ',
      avatarBg: '#DCFCE7',
      avatarColor: '#166534',
      birthDate: '06/04/2007',
      gender: 'Nam',
      parentName: 'Mai Văn Hùng',
      parentRole: 'Bố',
      parentPhone: '0947.990.011',
      gpa: 8.3,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024138',
      code: 'HS2024138',
      name: 'Trương Tấn Sang',
      email: 'tansang.12a1@academic.edu.vn',
      avatarText: 'TS',
      avatarBg: '#EDE9FE',
      avatarColor: '#6D28D9',
      birthDate: '21/03/2007',
      gender: 'Nam',
      parentName: 'Trương Văn Bính',
      parentRole: 'Bố',
      parentPhone: '0958.001.122',
      gpa: 8.7,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024139',
      code: 'HS2024139',
      name: 'Hồ Tấn Tài',
      email: 'tantai.12a1@academic.edu.vn',
      avatarText: 'TT',
      avatarBg: '#FEF3C7',
      avatarColor: '#92400E',
      birthDate: '06/11/2007',
      gender: 'Nam',
      parentName: 'Hồ Văn Nghĩa',
      parentRole: 'Bố',
      parentPhone: '0969.112.233',
      gpa: 8.5,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024140',
      code: 'HS2024140',
      name: 'Lý Thanh Thảo',
      email: 'thanhthao.12a1@academic.edu.vn',
      avatarText: 'TT',
      avatarBg: '#FCE7F3',
      avatarColor: '#9D174D',
      birthDate: '27/02/2007',
      gender: 'Nữ',
      parentName: 'Lý Quang Diệu',
      parentRole: 'Bố',
      parentPhone: '0970.223.344',
      gpa: 9.1,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024141',
      code: 'HS2024141',
      name: 'Vũ Văn Thanh',
      email: 'vanthanh.12a1@academic.edu.vn',
      avatarText: 'VT',
      avatarBg: '#E0E7FF',
      avatarColor: '#4338CA',
      birthDate: '14/04/2007',
      gender: 'Nam',
      parentName: 'Vũ Văn Hào',
      parentRole: 'Bố',
      parentPhone: '0981.334.455',
      gpa: 8.9,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024142',
      code: 'HS2024142',
      name: 'Nguyễn Văn Toàn',
      email: 'vantoan.12a1@academic.edu.vn',
      avatarText: 'VT',
      avatarBg: '#FFEDD5',
      avatarColor: '#9A3412',
      birthDate: '12/04/2007',
      gender: 'Nam',
      parentName: 'Nguyễn Văn Tạo',
      parentRole: 'Bố',
      parentPhone: '0912.445.566',
      gpa: 8.5,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024143',
      code: 'HS2024143',
      name: 'Bùi Tấn Trường',
      email: 'tantruong.12a1@academic.edu.vn',
      avatarText: 'TT',
      avatarBg: '#E0F2FE',
      avatarColor: '#0369A1',
      birthDate: '19/02/2007',
      gender: 'Nam',
      parentName: 'Bùi Văn Tuyên',
      parentRole: 'Bố',
      parentPhone: '0923.556.677',
      gpa: 8.3,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024144',
      code: 'HS2024144',
      name: 'Lương Xuân Trường',
      email: 'xuantruong.12a1@academic.edu.vn',
      avatarText: 'XT',
      avatarBg: '#EDE9FE',
      avatarColor: '#5B21B6',
      birthDate: '28/04/2007',
      gender: 'Nam',
      parentName: 'Lương Bách Chiến',
      parentRole: 'Bố',
      parentPhone: '0934.667.788',
      gpa: 9.2,
      rank: 'Xuất sắc',
      role: 'Thành viên',
      starred: false
    },
    {
      id: 'HS2024145',
      code: 'HS2024145',
      name: 'Võ Thị Tuyết',
      email: 'thituyet.12a1@academic.edu.vn',
      avatarText: 'TT',
      avatarBg: '#FCE7F3',
      avatarColor: '#BE185D',
      birthDate: '08/08/2007',
      gender: 'Nữ',
      parentName: 'Võ Thành Công',
      parentRole: 'Bố',
      parentPhone: '0945.778.899',
      gpa: 8.4,
      rank: 'Khá',
      role: 'Thành viên',
      starred: false
    }
  ];

  const [classStudents, setClassStudents] = useState(defaultClassStudents);
  const [studentSearch, setStudentSearch] = useState('');
  const [studentGenderFilter, setStudentGenderFilter] = useState('all');
  const [studentAcademicFilter, setStudentAcademicFilter] = useState('all');
  const [studentSortBy, setStudentSortBy] = useState('alphabet');
  const [studentSelectedIds, setStudentSelectedIds] = useState([]);

  // State for 'Chỉnh sửa thông tin học sinh' modal
  const [isEditStudentModalOpen, setIsEditStudentModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [editStudentForm, setEditStudentForm] = useState({
    name: '',
    code: '',
    birthDate: '',
    gender: 'Nam',
    email: '',
    parentName: '',
    parentRole: 'Bố',
    parentPhone: '',
    gpa: 8.5,
    rank: 'Giỏi'
  });

  // State for 'Thêm học sinh vào lớp' modal
  const [isAddStudentToClassModalOpen, setIsAddStudentToClassModalOpen] = useState(false);
  const [addStudentTab, setAddStudentTab] = useState('select'); // 'select' | 'create' | 'excel'
  const [availableCandidates, setAvailableCandidates] = useState([
    {
      id: 'HS2024201',
      code: 'HS2024201',
      name: 'Nguyễn Quỳnh Chi',
      email: 'quynhchi.cand@academic.edu.vn',
      avatarText: 'QC',
      avatarBg: '#FCE7F3',
      avatarColor: '#BE185D',
      birthDate: '15/05/2007',
      gender: 'Nữ',
      parentName: 'Nguyễn Văn Nam',
      parentRole: 'Bố',
      parentPhone: '0988.112.334',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 12',
      gpa: 8.8,
      rank: 'Giỏi'
    },
    {
      id: 'HS2024202',
      code: 'HS2024202',
      name: 'Phan Bảo Long',
      email: 'baolong.cand@academic.edu.vn',
      avatarText: 'BL',
      avatarBg: '#E0F2FE',
      avatarColor: '#0284C7',
      birthDate: '22/08/2007',
      gender: 'Nam',
      parentName: 'Phan Quốc Bảo',
      parentRole: 'Bố',
      parentPhone: '0977.223.445',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 12',
      gpa: 8.5,
      rank: 'Giỏi'
    },
    {
      id: 'HS2024203',
      code: 'HS2024203',
      name: 'Đoàn Phương Trinh',
      email: 'phuongtrinh.cand@academic.edu.vn',
      avatarText: 'PT',
      avatarBg: '#EDE9FE',
      avatarColor: '#6D28D9',
      birthDate: '10/11/2007',
      gender: 'Nữ',
      parentName: 'Đoàn Thế Vinh',
      parentRole: 'Bố',
      parentPhone: '0966.334.556',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 12',
      gpa: 9.1,
      rank: 'Xuất sắc'
    },
    {
      id: 'HS2024204',
      code: 'HS2024204',
      name: 'Trịnh Đình Quang',
      email: 'dinhquang.cand@academic.edu.vn',
      avatarText: 'ĐQ',
      avatarBg: '#DCFCE7',
      avatarColor: '#15803D',
      birthDate: '03/02/2007',
      gender: 'Nam',
      parentName: 'Trịnh Văn Quý',
      parentRole: 'Bố',
      parentPhone: '0912.445.667',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 11',
      gpa: 8.2,
      rank: 'Khá'
    },
    {
      id: 'HS2024205',
      code: 'HS2024205',
      name: 'Vũ Minh Khôi',
      email: 'minhkhoi.cand@academic.edu.vn',
      avatarText: 'MK',
      avatarBg: '#FEF3C7',
      avatarColor: '#B45309',
      birthDate: '18/06/2007',
      gender: 'Nam',
      parentName: 'Vũ Thành An',
      parentRole: 'Bố',
      parentPhone: '0903.556.778',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 11',
      gpa: 8.7,
      rank: 'Giỏi'
    },
    {
      id: 'HS2024206',
      code: 'HS2024206',
      name: 'Trần Ánh Tuyết',
      email: 'anhtuyet.cand@academic.edu.vn',
      avatarText: 'AT',
      avatarBg: '#FCE7F3',
      avatarColor: '#9D174D',
      birthDate: '29/03/2007',
      gender: 'Nữ',
      parentName: 'Trần Văn Tùng',
      parentRole: 'Bố',
      parentPhone: '0934.667.889',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 11',
      gpa: 8.6,
      rank: 'Giỏi'
    },
    {
      id: 'HS2024207',
      code: 'HS2024207',
      name: 'Hoàng Gia Huy',
      email: 'giahuy.cand@academic.edu.vn',
      avatarText: 'GH',
      avatarBg: '#E0E7FF',
      avatarColor: '#3730A3',
      birthDate: '14/09/2007',
      gender: 'Nam',
      parentName: 'Hoàng Văn Hải',
      parentRole: 'Bố',
      parentPhone: '0945.778.990',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 10',
      gpa: 8.9,
      rank: 'Giỏi'
    },
    {
      id: 'HS2024208',
      code: 'HS2024208',
      name: 'Phạm Bích Ngọc',
      email: 'bichngoc.cand@academic.edu.vn',
      avatarText: 'BN',
      avatarBg: '#F3E8FF',
      avatarColor: '#7E22CE',
      birthDate: '07/12/2007',
      gender: 'Nữ',
      parentName: 'Phạm Xuân Trường',
      parentRole: 'Bố',
      parentPhone: '0926.889.001',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 10',
      gpa: 8.4,
      rank: 'Khá'
    },
    {
      id: 'HS2024209',
      code: 'HS2024209',
      name: 'Ngô Tuấn Kiệt',
      email: 'tuankiet.cand@academic.edu.vn',
      avatarText: 'TK',
      avatarBg: '#CCFBF1',
      avatarColor: '#0F766E',
      birthDate: '21/04/2008',
      gender: 'Nam',
      parentName: 'Ngô Quốc Tuấn',
      parentRole: 'Bố',
      parentPhone: '0918.334.221',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 10',
      gpa: 8.8,
      rank: 'Giỏi'
    },
    {
      id: 'HS2024210',
      code: 'HS2024210',
      name: 'Lê Phương Linh',
      email: 'phuonglinh.cand@academic.edu.vn',
      avatarText: 'PL',
      avatarBg: '#FFE4E6',
      avatarColor: '#E11D48',
      birthDate: '15/10/2008',
      gender: 'Nữ',
      parentName: 'Lê Hoàng Nam',
      parentRole: 'Bố',
      parentPhone: '0972.115.889',
      status: 'Chưa xếp lớp',
      statusType: 'unassigned',
      currentGrade: 'Khối 10',
      gpa: 9.0,
      rank: 'Xuất sắc'
    }
  ]);

  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);
  const [candidateSearch, setCandidateSearch] = useState('');
  const [candidateGradeFilter, setCandidateGradeFilter] = useState('all');

  const [newStudentForm, setNewStudentForm] = useState({
    code: '',
    name: '',
    birthDate: '',
    gender: 'Nam',
    email: '',
    phone: '',
    parentName: '',
    parentRole: 'Bố',
    parentPhone: '',
    address: '',
    notes: ''
  });

  const [uploadedFileName, setUploadedFileName] = useState('');

  // Form state for new class
  const [newClass, setNewClass] = useState({
    code: '',
    name: '',
    specialty: '',
    grade: 'Khối 10',
    track: 'Chuẩn',
    capacity: 45,
    teacher: ''
  });

  // Assign teacher state
  const [teacherToAssign, setTeacherToAssign] = useState('');

  // Classes list matching reference mockup
  const [classes, setClasses] = useState([
    {
      id: 'LH12A01',
      code: 'LH12A01',
      name: '12A1 - Chuyên Toán',
      subSpecialty: 'Ban Khoa học Tự nhiên A',
      grade: 'Khối 12',
      gradeKey: 'k12',
      teacher: {
        name: 'ThS. Nguyễn Văn A',
        sub: 'Tổ Toán - Tin',
        avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=120'
      },
      currentStudents: 45,
      maxStudents: 45,
      track: 'Chuyên',
      trackKey: 'specialized',
      status: 'active', // 'active' | 'pending_teacher'
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH12A02',
      code: 'LH12A02',
      name: '12A2 - Chuyên Tin',
      subSpecialty: 'Ban Công nghệ & Thuật toán',
      grade: 'Khối 12',
      gradeKey: 'k12',
      teacher: {
        name: 'Cô Mai Lan',
        sub: 'Tổ Toán - Tin',
        avatarText: 'ML',
        avatarBg: '#EDE9FE',
        avatarColor: '#6D28D9'
      },
      currentStudents: 42,
      maxStudents: 45,
      track: 'Chuyên',
      trackKey: 'specialized',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH11B01',
      code: 'LH11B01',
      name: '11B1 - Tự nhiên',
      subSpecialty: 'Toán - Hóa - Sinh',
      grade: 'Khối 11',
      gradeKey: 'k11',
      teacher: {
        name: 'Thầy Lê Nguyên',
        sub: 'Tổ Hóa - Sinh',
        avatarText: 'LN',
        avatarBg: '#F3ECFF',
        avatarColor: '#5B32A8'
      },
      currentStudents: 44,
      maxStudents: 45,
      track: 'Chuẩn',
      trackKey: 'standard',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH11B02',
      code: 'LH11B02',
      name: '11B2 - Vật lý cơ bản',
      subSpecialty: 'Toán - Lý - Anh',
      grade: 'Khối 11',
      gradeKey: 'k11',
      teacher: {
        name: 'Cô Thu Hương',
        sub: 'Tổ Vật lý',
        avatarText: 'TH',
        avatarBg: '#E0E7FF',
        avatarColor: '#3730A3'
      },
      currentStudents: 40,
      maxStudents: 45,
      track: 'Chuẩn',
      trackKey: 'standard',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH10A03',
      code: 'LH10A03',
      name: '10A3 - Tiếng Anh IELTS',
      subSpecialty: 'Tăng cường ngoại ngữ',
      grade: 'Khối 10',
      gradeKey: 'k10',
      teacher: {
        name: 'Thầy Hoàng Nam',
        sub: 'Tổ Ngoại ngữ',
        avatarText: 'HN',
        avatarBg: '#FCE7F3',
        avatarColor: '#BE185D'
      },
      currentStudents: 38,
      maxStudents: 40,
      track: 'Song ngữ',
      trackKey: 'bilingual',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH10A08',
      code: 'LH10A08',
      name: '10A8 - Xã hội',
      subSpecialty: 'Văn - Sử - Địa',
      grade: 'Khối 10',
      gradeKey: 'k10',
      teacher: null, // Unassigned
      currentStudents: 43,
      maxStudents: 45,
      track: 'Chuẩn',
      trackKey: 'standard',
      status: 'pending_teacher',
      statusLabel: 'Chờ phân công GV',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH11B03',
      code: 'LH11B03',
      name: '11B3 - Xã hội D01',
      subSpecialty: 'Văn - Sử - Địa',
      grade: 'Khối 11',
      gradeKey: 'k11',
      teacher: {
        name: 'Cô Trần Thị Mai',
        sub: 'Tổ Ngữ văn',
        avatarText: 'TM',
        avatarBg: '#FCE7F3',
        avatarColor: '#BE185D'
      },
      currentStudents: 41,
      maxStudents: 45,
      track: 'Chuẩn',
      trackKey: 'standard',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH12A03',
      code: 'LH12A03',
      name: '12A3 - Tiếng Anh D01',
      subSpecialty: 'Toán - Văn - Anh',
      grade: 'Khối 12',
      gradeKey: 'k12',
      teacher: {
        name: 'Thầy Hoàng Nam',
        sub: 'Tổ Ngoại ngữ',
        avatarText: 'HN',
        avatarBg: '#E0E7FF',
        avatarColor: '#3730A3'
      },
      currentStudents: 44,
      maxStudents: 45,
      track: 'Song ngữ',
      trackKey: 'bilingual',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH10A01',
      code: 'LH10A01',
      name: '10A1 - Chuyên Hóa',
      subSpecialty: 'Hóa học chuyên sâu',
      grade: 'Khối 10',
      gradeKey: 'k10',
      teacher: {
        name: 'Thầy Lê Nguyên',
        sub: 'Tổ Hóa - Sinh',
        avatarText: 'LN',
        avatarBg: '#F3ECFF',
        avatarColor: '#5B32A8'
      },
      currentStudents: 39,
      maxStudents: 40,
      track: 'Chuyên',
      trackKey: 'specialized',
      status: 'active',
      statusLabel: 'Đang học',
      academicYear: '2024 - 2025'
    },
    {
      id: 'LH10A05',
      code: 'LH10A05',
      name: '10A5 - Tự nhiên',
      subSpecialty: 'Toán - Lý - Hóa',
      grade: 'Khối 10',
      gradeKey: 'k10',
      teacher: null, // Unassigned
      currentStudents: 42,
      maxStudents: 45,
      track: 'Chuẩn',
      trackKey: 'standard',
      status: 'pending_teacher',
      statusLabel: 'Chờ phân công GV',
      academicYear: '2024 - 2025'
    }
  ]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  // Filtered classes calculation
  const filteredClasses = useMemo(() => {
    return classes.filter(cls => {
      // Tab filter
      if (activeTab === 'k10' && cls.gradeKey !== 'k10') return false;
      if (activeTab === 'k11' && cls.gradeKey !== 'k11') return false;
      if (activeTab === 'k12' && cls.gradeKey !== 'k12') return false;
      if (activeTab === 'specialized' && cls.trackKey !== 'specialized') return false;

      // Grade dropdown filter
      if (gradeFilter !== 'all') {
        if (gradeFilter === 'k10' && cls.gradeKey !== 'k10') return false;
        if (gradeFilter === 'k11' && cls.gradeKey !== 'k11') return false;
        if (gradeFilter === 'k12' && cls.gradeKey !== 'k12') return false;
      }

      // Teacher status filter
      if (teacherStatusFilter === 'assigned' && !cls.teacher) return false;
      if (teacherStatusFilter === 'unassigned' && cls.teacher) return false;

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();
        const matchCode = cls.code.toLowerCase().includes(q);
        const matchName = cls.name.toLowerCase().includes(q);
        const matchSub = cls.subSpecialty.toLowerCase().includes(q);
        const matchTeacher = cls.teacher?.name.toLowerCase().includes(q);
        if (!matchCode && !matchName && !matchSub && !matchTeacher) return false;
      }

      return true;
    });
  }, [classes, activeTab, gradeFilter, teacherStatusFilter, searchQuery]);

  // Paginated classes calculation (max 10 rows per page by default)
  const paginatedClasses = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredClasses.slice(startIndex, startIndex + pageSize);
  }, [filteredClasses, currentPage, pageSize]);

  // Selection handlers
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(filteredClasses.map(c => c.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]);
  };

  // Dialog Students Memo & Handlers
  const filteredClassStudents = useMemo(() => {
    return classStudents.filter(st => {
      if (studentGenderFilter !== 'all' && st.gender !== studentGenderFilter) return false;
      if (studentAcademicFilter !== 'all' && st.rank !== studentAcademicFilter) return false;
      if (studentSearch.trim()) {
        const q = studentSearch.trim().toLowerCase();
        const matchName = st.name.toLowerCase().includes(q);
        const matchCode = st.code.toLowerCase().includes(q);
        const matchParent = st.parentName.toLowerCase().includes(q);
        const matchPhone = st.parentPhone.includes(q);
        if (!matchName && !matchCode && !matchParent && !matchPhone) return false;
      }
      return true;
    }).sort((a, b) => {
      if (studentSortBy === 'gpa_desc') {
        const gpaDiff = b.gpa - a.gpa;
        if (gpaDiff !== 0) return gpaDiff;
      }
      return compareVietnameseNames(a.name, b.name);
    });
  }, [classStudents, studentSearch, studentGenderFilter, studentAcademicFilter, studentSortBy]);

  const handleToggleStarStudent = (studentId) => {
    setClassStudents(prev => prev.map(s => s.id === studentId ? { ...s, starred: !s.starred } : s));
  };

  const handleSelectAllStudents = (e) => {
    if (e.target.checked) {
      setStudentSelectedIds(filteredClassStudents.map(s => s.id));
    } else {
      setStudentSelectedIds([]);
    }
  };

  const handleToggleSelectStudent = (id) => {
    setStudentSelectedIds(prev => prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]);
  };

  // Candidate students filtering & handlers for 'Thêm học sinh vào lớp'
  const filteredCandidates = useMemo(() => {
    return availableCandidates.filter(c => {
      if (candidateGradeFilter !== 'all' && c.currentGrade !== candidateGradeFilter) return false;
      if (candidateSearch.trim()) {
        const q = candidateSearch.trim().toLowerCase();
        const matchName = c.name.toLowerCase().includes(q);
        const matchCode = c.code.toLowerCase().includes(q);
        const matchPhone = c.parentPhone.includes(q);
        if (!matchName && !matchCode && !matchPhone) return false;
      }
      return true;
    }).sort((a, b) => compareVietnameseNames(a.name, b.name));
  }, [availableCandidates, candidateSearch, candidateGradeFilter]);

  const handleToggleSelectCandidate = (id) => {
    setSelectedCandidateIds(prev => prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]);
  };

  const handleSelectAllCandidates = (e) => {
    if (e.target.checked) {
      setSelectedCandidateIds(filteredCandidates.map(c => c.id));
    } else {
      setSelectedCandidateIds([]);
    }
  };

  const handleAddCandidatesToClass = () => {
    if (selectedCandidateIds.length === 0 || !selectedClass) return;

    const toAdd = availableCandidates.filter(c => selectedCandidateIds.includes(c.id));
    const newStudentsToAdd = toAdd.map(c => ({
      id: c.id,
      code: c.code,
      name: c.name,
      email: c.email,
      avatarText: c.avatarText,
      avatarBg: c.avatarBg,
      avatarColor: c.avatarColor,
      birthDate: c.birthDate,
      gender: c.gender,
      parentName: c.parentName,
      parentRole: c.parentRole,
      parentPhone: c.parentPhone,
      gpa: c.gpa || 8.5,
      rank: c.rank || 'Giỏi',
      role: 'Thành viên',
      starred: false
    }));

    setClassStudents(prev => [...prev, ...newStudentsToAdd]);
    setAvailableCandidates(prev => prev.filter(c => !selectedCandidateIds.includes(c.id)));

    setClasses(prev => prev.map(cls => cls.id === selectedClass.id ? {
      ...cls,
      currentStudents: cls.currentStudents + newStudentsToAdd.length
    } : cls));

    setSelectedCandidateIds([]);
    setIsAddStudentToClassModalOpen(false);
    showToast(`Đã thêm thành công ${newStudentsToAdd.length} học sinh vào lớp ${selectedClass.name}!`);
  };

  const handleCreateAndAddStudent = (e) => {
    e.preventDefault();
    if (!newStudentForm.name.trim() || !newStudentForm.parentPhone.trim()) {
      alert('Vui lòng điền đầy đủ họ tên học sinh và số điện thoại phụ huynh.');
      return;
    }

    const nextNum = classStudents.length + 101;
    const generatedCode = newStudentForm.code.trim() || `HS2024${nextNum}`;
    const nameParts = newStudentForm.name.trim().split(/\s+/);
    const lastNamePart = nameParts[nameParts.length - 1] || 'HS';
    const firstTwoLetters = (nameParts[0]?.[0] || 'H') + (lastNamePart[0] || 'S');

    const createdStudent = {
      id: generatedCode,
      code: generatedCode,
      name: newStudentForm.name.trim(),
      email: newStudentForm.email.trim() || `${lastNamePart.toLowerCase()}.${generatedCode.toLowerCase()}@academic.edu.vn`,
      avatarText: firstTwoLetters.toUpperCase(),
      avatarBg: '#EDE9FE',
      avatarColor: '#5B32A8',
      birthDate: newStudentForm.birthDate || '01/01/2007',
      gender: newStudentForm.gender,
      parentName: newStudentForm.parentName.trim() || 'Phụ huynh học sinh',
      parentRole: newStudentForm.parentRole || 'Bố',
      parentPhone: newStudentForm.parentPhone.trim(),
      gpa: 8.5,
      rank: 'Giỏi',
      role: 'Thành viên',
      starred: false
    };

    setClassStudents(prev => [...prev, createdStudent]);

    setClasses(prev => prev.map(cls => cls.id === selectedClass.id ? {
      ...cls,
      currentStudents: cls.currentStudents + 1
    } : cls));

    setNewStudentForm({
      code: '',
      name: '',
      birthDate: '',
      gender: 'Nam',
      email: '',
      phone: '',
      parentName: '',
      parentRole: 'Bố',
      parentPhone: '',
      address: '',
      notes: ''
    });

    setIsAddStudentToClassModalOpen(false);
    showToast(`Đã tạo và thêm học sinh ${createdStudent.name} vào lớp ${selectedClass.name}!`);
  };

  const handleImportExcelStudents = () => {
    if (!uploadedFileName) {
      alert('Vui lòng chọn tập tin Excel (.xlsx, .csv).');
      return;
    }

    const imported = [
      {
        id: `HS2024${classStudents.length + 101}`,
        code: `HS2024${classStudents.length + 101}`,
        name: 'Trần Gia Hưng',
        email: `giahung.${selectedClass.name.split(' ')[0].toLowerCase()}@academic.edu.vn`,
        avatarText: 'GH',
        avatarBg: '#DCFCE7',
        avatarColor: '#15803D',
        birthDate: '14/05/2007',
        gender: 'Nam',
        parentName: 'Trần Văn Hoàng',
        parentRole: 'Bố',
        parentPhone: '0979.888.777',
        gpa: 8.8,
        rank: 'Giỏi',
        role: 'Thành viên',
        starred: false
      },
      {
        id: `HS2024${classStudents.length + 102}`,
        code: `HS2024${classStudents.length + 102}`,
        name: 'Đặng Ngọc Diệp',
        email: `ngocdiep.${selectedClass.name.split(' ')[0].toLowerCase()}@academic.edu.vn`,
        avatarText: 'ND',
        avatarBg: '#FCE7F3',
        avatarColor: '#BE185D',
        birthDate: '26/10/2007',
        gender: 'Nữ',
        parentName: 'Đặng Quốc Bảo',
        parentRole: 'Bố',
        parentPhone: '0988.666.555',
        gpa: 9.1,
        rank: 'Xuất sắc',
        role: 'Thành viên',
        starred: false
      }
    ];

    setClassStudents(prev => [...prev, ...imported]);

    setClasses(prev => prev.map(cls => cls.id === selectedClass.id ? {
      ...cls,
      currentStudents: cls.currentStudents + imported.length
    } : cls));

    setUploadedFileName('');
    setIsAddStudentToClassModalOpen(false);
    showToast(`Đã nhập thành công ${imported.length} học sinh từ tập tin ${uploadedFileName} vào lớp ${selectedClass.name}!`);
  };

  // Edit student handlers
  const handleOpenEditStudent = (student) => {
    setEditingStudent(student);
    setEditStudentForm({
      name: student.name,
      code: student.code,
      birthDate: student.birthDate,
      gender: student.gender,
      email: student.email,
      parentName: student.parentName,
      parentRole: student.parentRole,
      parentPhone: student.parentPhone,
      gpa: student.gpa,
      rank: student.rank
    });
    setIsEditStudentModalOpen(true);
  };

  const handleSaveEditStudent = (e) => {
    e.preventDefault();
    if (!editingStudent) return;

    setClassStudents(prev => prev.map(s => {
      if (s.id === editingStudent.id) {
        return {
          ...s,
          name: editStudentForm.name.trim(),
          birthDate: editStudentForm.birthDate,
          gender: editStudentForm.gender,
          email: editStudentForm.email.trim(),
          parentName: editStudentForm.parentName.trim(),
          parentRole: editStudentForm.parentRole,
          parentPhone: editStudentForm.parentPhone.trim(),
          gpa: Number(editStudentForm.gpa) || s.gpa,
          rank: editStudentForm.rank
        };
      }
      return s;
    }));

    setIsEditStudentModalOpen(false);
    setEditingStudent(null);
    showToast(`Đã cập nhật thông tin học sinh ${editStudentForm.name} thành công!`);
  };

  // Assign teacher action
  const handleAssignTeacherSubmit = (e) => {
    e.preventDefault();
    if (!teacherToAssign || !selectedClass) return;

    setClasses(prev => prev.map(cls => {
      if (cls.id === selectedClass.id) {
        return {
          ...cls,
          teacher: {
            name: teacherToAssign,
            sub: 'Tổ Giáo viên Phân công',
            avatarText: teacherToAssign.split(' ').slice(-1)[0][0] || 'GV',
            avatarBg: '#EDE9FE',
            avatarColor: '#5B32A8'
          },
          status: 'active',
          statusLabel: 'Đang học'
        };
      }
      return cls;
    }));

    setIsAssignModalOpen(false);
    showToast(`Đã phân công ${teacherToAssign} làm GVCN lớp ${selectedClass.name}!`);
  };

  // Add new class submit
  const handleAddClassSubmit = (e) => {
    e.preventDefault();
    if (!newClass.name) {
      alert('Vui lòng nhập tên lớp học.');
      return;
    }

    const code = `LH${newClass.name.replace(/[^0-9A-Z]/gi, '').slice(0, 5) || '10A9'}`;
    const created = {
      id: code,
      code: code,
      name: newClass.name,
      subSpecialty: newClass.specialty || 'Học tập chuẩn',
      grade: newClass.grade,
      gradeKey: newClass.grade.includes('10') ? 'k10' : newClass.grade.includes('11') ? 'k11' : 'k12',
      teacher: newClass.teacher ? {
        name: newClass.teacher,
        sub: 'Tổ Phân công',
        avatarText: newClass.teacher.split(' ').slice(-1)[0][0] || 'GV',
        avatarBg: '#EDE9FE',
        avatarColor: '#5B32A8'
      } : null,
      currentStudents: 0,
      maxStudents: Number(newClass.capacity) || 45,
      track: newClass.track,
      trackKey: newClass.track === 'Chuyên' ? 'specialized' : newClass.track === 'Song ngữ' ? 'bilingual' : 'standard',
      status: newClass.teacher ? 'active' : 'pending_teacher',
      statusLabel: newClass.teacher ? 'Đang học' : 'Chờ phân công GV',
      academicYear: '2024 - 2025'
    };

    setClasses(prev => [created, ...prev]);
    setIsAddModalOpen(false);
    showToast(`Đã tạo thành công lớp học ${created.name}!`);
    setNewClass({
      code: '',
      name: '',
      specialty: '',
      grade: 'Khối 10',
      track: 'Chuẩn',
      capacity: 45,
      teacher: ''
    });
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setGradeFilter('all');
    setTeacherStatusFilter('all');
    setActiveTab('all');
    showToast('Đã đặt lại tất cả bộ lọc về mặc định.');
  };

  const removeFilterTag = (tagId) => {
    setFilterTags(prev => prev.filter(t => t.id !== tagId));
  };

  return (
    <div className="admin-classes-page-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="admin-toast">
          <CheckCircle2 size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Section */}
      <section className="classes-page-header">
        <div className="classes-header-title-block">
          <div className="classes-header-title-row">
            <span className="classes-title-accent-bar"></span>
            <h1 className="classes-page-title">Quản lý trường lớp</h1>
          </div>
          <p className="classes-page-subtitle">
            Quản lý danh sách lớp học, phân công giáo viên chủ nhiệm và sĩ số học sinh các khối.
          </p>
        </div>

        <div className="classes-header-actions">
          <button 
            type="button" 
            className="btn-classes-export"
            onClick={() => setIsExportModalOpen(true)}
          >
            <Download size={16} strokeWidth={2} />
            <span>Xuất dữ liệu Excel</span>
          </button>

          <button 
            type="button" 
            className="btn-classes-add"
            onClick={() => setIsAddModalOpen(true)}
          >
            <Plus size={17} strokeWidth={2.4} />
            <span>Thêm lớp học mới</span>
          </button>
        </div>
      </section>

      {/* 2. Tab Pills Row */}
      <section className="classes-tabs-section">
        <div className="classes-tabs-list">
          <button 
            type="button" 
            className={`classes-tab-pill ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            Tất cả lớp (64)
          </button>
          <button 
            type="button" 
            className={`classes-tab-pill ${activeTab === 'k10' ? 'active' : ''}`}
            onClick={() => setActiveTab('k10')}
          >
            Khối 10 (22)
          </button>
          <button 
            type="button" 
            className={`classes-tab-pill ${activeTab === 'k11' ? 'active' : ''}`}
            onClick={() => setActiveTab('k11')}
          >
            Khối 11 (20)
          </button>
          <button 
            type="button" 
            className={`classes-tab-pill ${activeTab === 'k12' ? 'active' : ''}`}
            onClick={() => setActiveTab('k12')}
          >
            Khối 12 (22)
          </button>
        </div>

        <div className="classes-selection-counter-block">
          <span className="classes-selected-count-text">
            Đã chọn: <strong>{selectedIds.length}</strong>
          </span>
          <button 
            type="button" 
            className="classes-refresh-icon-btn" 
            title="Làm mới danh sách"
            onClick={() => {
              setSelectedIds([]);
              showToast('Đã làm mới danh sách lớp học.');
            }}
          >
            <RotateCw size={15} />
          </button>
        </div>
      </section>

      {/* 4. Filter Bar */}
      <section className="classes-filter-bar-container">
        <div className="classes-filter-bar">
          {/* Search Box */}
          <div className="filter-search-box">
            <Search size={16} className="filter-search-icon" />
            <input 
              type="text" 
              className="filter-search-input" 
              placeholder="Tìm theo tên lớp, mã, GVCN..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button 
                type="button" 
                className="filter-search-clear"
                onClick={() => setSearchQuery('')}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Grade Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={gradeFilter}
              onChange={e => setGradeFilter(e.target.value)}
            >
              <option value="all">Tất cả khối lớp</option>
              <option value="k10">Khối 10</option>
              <option value="k11">Khối 11</option>
              <option value="k12">Khối 12</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>


          {/* Teacher Status Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={teacherStatusFilter}
              onChange={e => setTeacherStatusFilter(e.target.value)}
            >
              <option value="all">Tình trạng GVCN</option>
              <option value="assigned">Đã phân công</option>
              <option value="unassigned">Chưa phân công</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Reset Filters Icon Button */}
          <button 
            type="button" 
            className="filter-btn-reset" 
            title="Đặt lại bộ lọc"
            onClick={handleResetFilters}
          >
            <RotateCw size={15} />
          </button>
        </div>
      </section>

      {/* 5. Active Filters Tag Row */}
      {filterTags.length > 0 && (
        <section className="classes-active-tags-row">
          <span className="tags-label">Đang lọc theo:</span>
          <div className="tags-list">
            {filterTags.map(tag => (
              <span key={tag.id} className="active-tag-chip">
                <span>{tag.label}</span>
                <button type="button" onClick={() => removeFilterTag(tag.id)}>
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
          <button 
            type="button" 
            className="tags-clear-all" 
            onClick={() => {
              setFilterTags([]);
              handleResetFilters();
            }}
          >
            Xóa tất cả
          </button>
        </section>
      )}

      {/* 6. Classes Data Table */}
      <section className="classes-table-card">
        <div className="classes-table-scroll-wrapper">
          <table className="classes-table">
            <thead>
              <tr>
                <th className="col-checkbox">
                  <input 
                    type="checkbox" 
                    className="custom-table-checkbox"
                    checked={filteredClasses.length > 0 && selectedIds.length === filteredClasses.length}
                    onChange={handleSelectAll}
                  />
                </th>
                <th className="col-code">MÃ LỚP</th>
                <th className="col-name">TÊN LỚP HỌC</th>
                <th className="col-grade">KHỐI</th>
                <th className="col-teacher">GIÁO VIÊN CHỦ NHIỆM</th>
                <th className="col-capacity text-center">SĨ SỐ / TỐI ĐA</th>
                <th className="col-status">TRẠNG THÁI</th>
                <th className="col-actions text-right">THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {filteredClasses.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-table-cell">
                    <AlertCircle size={28} className="empty-icon" />
                    <p>Không tìm thấy lớp học nào phù hợp với bộ lọc hiện tại.</p>
                  </td>
                </tr>
              ) : (
                paginatedClasses.map(cls => {
                  const isSelected = selectedIds.includes(cls.id);
                  return (
                    <tr 
                      key={cls.id} 
                      className={`classes-table-row ${isSelected ? 'row-selected' : ''}`}
                      onClick={(e) => {
                        if (e.target.closest('.col-checkbox') || e.target.closest('.table-row-actions')) return;
                        setSelectedClass(cls);
                        setIsViewModalOpen(true);
                      }}
                      title="Nhấn để xem chi tiết lớp học"
                    >
                      {/* Checkbox */}
                      <td className="col-checkbox">
                        <input 
                          type="checkbox" 
                          className="custom-table-checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelect(cls.id)}
                        />
                      </td>

                      {/* Code identifier link */}
                      <td className="col-code">
                        <button 
                          type="button" 
                          className="class-code-link"
                          onClick={() => {
                            setSelectedClass(cls);
                            setIsViewModalOpen(true);
                          }}
                        >
                          {cls.code}
                        </button>
                      </td>

                      {/* Class Name & Specialty */}
                      <td className="col-name">
                        <div className="class-name-block">
                          <span 
                            className="class-primary-name"
                            onClick={() => {
                              setSelectedClass(cls);
                              setIsViewModalOpen(true);
                            }}
                          >
                            {cls.name}
                          </span>
                          <span className="class-sub-specialty">{cls.subSpecialty}</span>
                        </div>
                      </td>

                      {/* Grade */}
                      <td className="col-grade">
                        <div className="grade-badge-cell">
                          <span className="grade-text-main">{cls.grade}</span>
                        </div>
                      </td>

                      {/* Homeroom Teacher */}
                      <td className="col-teacher">
                        {cls.teacher ? (
                          <div className="table-teacher-block">
                            {cls.teacher.avatarUrl ? (
                              <img src={cls.teacher.avatarUrl} alt={cls.teacher.name} className="teacher-avatar-img" />
                            ) : (
                              <div 
                                className="teacher-avatar-badge"
                                style={{ backgroundColor: cls.teacher.avatarBg, color: cls.teacher.avatarColor }}
                              >
                                {cls.teacher.avatarText}
                              </div>
                            )}
                            <div className="teacher-meta-block">
                              <span className="teacher-full-name">{cls.teacher.name}</span>
                              <span className="teacher-sub-dept">{cls.teacher.sub}</span>
                            </div>
                          </div>
                        ) : (
                          <button 
                            type="button" 
                            className="btn-unassigned-teacher-badge"
                            onClick={() => {
                              setSelectedClass(cls);
                              setIsAssignModalOpen(true);
                            }}
                          >
                            <AlertTriangle size={13} />
                            <span>Chưa phân công</span>
                          </button>
                        )}
                      </td>

                      {/* Sĩ số / Tối đa Capacity Capsule */}
                      <td className="col-capacity text-center">
                        <div className="capacity-capsule">
                          <span className="capacity-current">{cls.currentStudents}</span>
                          <span className="capacity-divider">/</span>
                          <span className="capacity-max">{cls.maxStudents}</span>
                          <span className="capacity-unit">HS</span>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="col-status">
                        {cls.status === 'active' ? (
                          <span className="class-status-pill active">
                            <span className="status-dot green"></span>
                            {cls.statusLabel}
                          </span>
                        ) : (
                          <span className="class-status-pill pending">
                            <span className="status-dot amber"></span>
                            {cls.statusLabel}
                          </span>
                        )}
                      </td>

                      {/* Action Icons */}
                      <td className="col-actions text-right">
                        <div className="table-row-actions">
                          {/* View details */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Xem chi tiết lớp học"
                            onClick={() => {
                              setSelectedClass(cls);
                              setIsViewModalOpen(true);
                            }}
                          >
                            <Eye size={17} />
                          </button>

                          {/* Edit class */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Chỉnh sửa thông tin"
                            onClick={() => {
                              setSelectedClass(cls);
                              setIsEditModalOpen(true);
                            }}
                          >
                            <Edit2 size={16} />
                          </button>

                          {/* Quick assign button if unassigned */}
                          {!cls.teacher && (
                            <button 
                              type="button" 
                              className="table-action-icon-btn text-accent" 
                              title="Phân công GVCN"
                              onClick={() => {
                                setSelectedClass(cls);
                                setIsAssignModalOpen(true);
                              }}
                            >
                              <UserPlus size={16} />
                            </button>
                          )}

                          {/* More options */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Tùy chọn khác"
                            onClick={() => {
                              if (window.confirm(`Bạn có chắc chắn muốn lưu trữ hoặc vô hiệu hóa lớp ${cls.name}?`)) {
                                showToast(`Lớp ${cls.name} đã được lưu trữ (Soft Delete).`);
                              }
                            }}
                          >
                            <MoreVertical size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 7. Pagination Footer */}
        <div className="classes-pagination-footer">
          <div className="pagination-info">
            Hiển thị <strong>{filteredClasses.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, filteredClasses.length)}</strong> trong số <strong>64</strong> lớp học
          </div>

          <div className="pagination-controls">
            <div className="pagination-page-size-selector">
              <span>Hàng trên trang:</span>
              <select 
                value={pageSize}
                onChange={e => setPageSize(Number(e.target.value))}
                className="page-size-select"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="pagination-nav-buttons">
              <button 
                type="button" 
                className="page-nav-btn" 
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              >
                <ChevronLeft size={16} />
              </button>
              <button type="button" className="page-num-btn active">1</button>
              <button type="button" className="page-num-btn">2</button>
              <button type="button" className="page-num-btn">3</button>
              <span className="page-num-ellipsis">...</span>
              <button type="button" className="page-num-btn">7</button>
              <button 
                type="button" 
                className="page-nav-btn"
                onClick={() => setCurrentPage(p => p + 1)}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 8. Bottom Smart Schedule Banner */}
      <section className="classes-schedule-banner">
        <div className="schedule-banner-left">
          <div className="schedule-banner-icon-box">
            <LayoutGrid size={22} />
          </div>
          <div className="schedule-banner-text">
            <h4 className="schedule-banner-title">
              Cần phân công giáo viên chủ nhiệm hàng loạt hoặc sắp xếp thời khóa biểu tự động?
            </h4>
            <p className="schedule-banner-desc">
              Hệ thống hỗ trợ kiểm tra phân công và tự động gán giáo viên theo tổ bộ môn.
            </p>
          </div>
        </div>

        <div className="schedule-banner-actions">
          <button 
            type="button" 
            className="btn-download-map"
            onClick={() => showToast('Đang tạo và tải danh sách lớp học (PDF)...')}
          >
            Tải danh sách lớp học (PDF/Excel)
          </button>
        </div>
      </section>

      {/* MODAL: Thêm lớp học mới */}
      {isAddModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsAddModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Thêm lớp học mới</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsAddModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAddClassSubmit} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Tên lớp học *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="Ví dụ: 10A1 - Chuyên Toán" 
                  value={newClass.name}
                  onChange={e => setNewClass(p => ({ ...p, name: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Ban / Chuyên đề học tập</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="Ví dụ: Ban Khoa học Tự nhiên" 
                  value={newClass.specialty}
                  onChange={e => setNewClass(p => ({ ...p, specialty: e.target.value }))}
                />
              </div>

              <div className="admin-form-row">
                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Khối lớp</label>
                  <select 
                    className="admin-form-select"
                    value={newClass.grade}
                    onChange={e => setNewClass(p => ({ ...p, grade: e.target.value }))}
                  >
                    <option value="Khối 10">Khối 10</option>
                    <option value="Khối 11">Khối 11</option>
                    <option value="Khối 12">Khối 12</option>
                  </select>
                </div>

                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Hệ đào tạo</label>
                  <select 
                    className="admin-form-select"
                    value={newClass.track}
                    onChange={e => setNewClass(p => ({ ...p, track: e.target.value }))}
                  >
                    <option value="Chuẩn">Chuẩn</option>
                    <option value="Chuyên">Chuyên</option>
                    <option value="Song ngữ">Song ngữ</option>
                  </select>
                </div>
              </div>

              <div className="admin-form-row">
                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Sĩ số tối đa</label>
                  <input 
                    type="number" 
                    className="admin-form-input" 
                    value={newClass.capacity}
                    onChange={e => setNewClass(p => ({ ...p, capacity: e.target.value }))}
                  />
                </div>

                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Giáo viên chủ nhiệm (nếu có)</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    placeholder="Nhập tên giáo viên hoặc chọn sau" 
                    value={newClass.teacher}
                    onChange={e => setNewClass(p => ({ ...p, teacher: e.target.value }))}
                  />
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsAddModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary">
                  Tạo lớp học
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Phân công Giáo viên chủ nhiệm */}
      {isAssignModalOpen && selectedClass && (
        <div className="admin-modal-backdrop" onClick={() => setIsAssignModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Phân công GVCN cho lớp {selectedClass.name}</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsAssignModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAssignTeacherSubmit} className="admin-modal-body">
              <p className="admin-modal-desc">
                Chọn giáo viên phụ trách chủ nhiệm lớp <strong>{selectedClass.name}</strong>.
              </p>

              <div className="admin-form-group">
                <label className="admin-form-label">Chọn giáo viên bộ môn</label>
                <select 
                  className="admin-form-select"
                  value={teacherToAssign}
                  onChange={e => setTeacherToAssign(e.target.value)}
                  required
                >
                  <option value="">-- Chọn giáo viên từ danh sách --</option>
                  <option value="ThS. Nguyễn Văn A">ThS. Nguyễn Văn A (Tổ Toán - Tin)</option>
                  <option value="Cô Mai Lan">Cô Mai Lan (Tổ Toán - Tin)</option>
                  <option value="Thầy Lê Nguyên">Thầy Lê Nguyên (Tổ Hóa - Sinh)</option>
                  <option value="Cô Thu Hương">Cô Thu Hương (Tổ Vật lý)</option>
                  <option value="Thầy Hoàng Nam">Thầy Hoàng Nam (Tổ Ngoại ngữ)</option>
                  <option value="Cô Trần Thị Mai">Cô Trần Thị Mai (Tổ Ngữ văn)</option>
                </select>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsAssignModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary" disabled={!teacherToAssign}>
                  Lưu phân công
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Xem chi tiết lớp học (Full-screen Dialog như Hình 1) */}
      {isViewModalOpen && selectedClass && (
        <div className="class-dialog-backdrop" onClick={() => setIsViewModalOpen(false)}>
          <div className="class-dialog-card" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="class-dialog-header">
              <div className="dialog-header-left">
                <div className="dialog-header-icon-box">
                  <GraduationCap size={24} />
                </div>
                <div className="dialog-header-titles">
                  <div className="dialog-title-line">
                    <h2 className="dialog-main-title">Thông tin Lớp học: {selectedClass.name}</h2>
                    <span className="dialog-grade-pill">{selectedClass.grade}</span>
                  </div>
                  <div className="dialog-meta-line">
                    <span className="dialog-spec-pill">{selectedClass.subSpecialty || 'Ban KHTN A'}</span>
                    <span className="dialog-status-badge">
                      <span className="dialog-status-dot"></span>
                      Đang học
                    </span>
                    <span className="dialog-meta-divider">•</span>
                    <span className="dialog-meta-text">
                      <Calendar size={13} className="meta-icon" />
                      Niên khóa: {selectedClass.academicYear}
                    </span>
                    <span className="dialog-meta-divider">•</span>
                    <span className="dialog-meta-text">
                      Mã lớp: <strong>{selectedClass.code}</strong>
                    </span>
                  </div>
                </div>
              </div>

              <div className="dialog-header-right">
                <button 
                  type="button" 
                  className="btn-dialog-export"
                  onClick={() => showToast(`Đang xuất danh sách lớp ${selectedClass.name} (Excel/PDF)...`)}
                >
                  <Download size={15} />
                  <span>Xuất danh sách (Excel/PDF)</span>
                </button>
                <button 
                  type="button" 
                  className="btn-dialog-add-student"
                  onClick={() => setIsAddStudentToClassModalOpen(true)}
                >
                  <UserPlus size={15} />
                  <span>Thêm học sinh vào lớp</span>
                </button>
                <button 
                  type="button" 
                  className="btn-dialog-close" 
                  title="Đóng hộp thoại"
                  onClick={() => setIsViewModalOpen(false)}
                >
                  <X size={19} />
                </button>
              </div>
            </div>

            {/* Dialog Body */}
            <div className="class-dialog-body">
              {/* 4 Stat Cards Row */}
              <div className="class-dialog-stats-grid">
                {/* 1. GVCN */}
                <div className="stat-card-teacher-box">
                  {selectedClass.teacher?.avatarUrl ? (
                    <img src={selectedClass.teacher.avatarUrl} alt="" className="teacher-box-avatar" />
                  ) : (
                    <div className="teacher-box-avatar-text">
                      {selectedClass.teacher?.avatarText || 'GV'}
                    </div>
                  )}
                  <div className="teacher-box-info">
                    <div className="teacher-box-title-row">
                      <span className="teacher-box-name">{selectedClass.teacher ? selectedClass.teacher.name : 'ThS. Nguyễn Văn A'}</span>
                      <span className="teacher-box-badge">GVCN</span>
                    </div>
                    <div className="teacher-box-contact-row">
                      <span>0912.345.678</span>
                      <span className="contact-dot">•</span>
                      <span>nguyenvana@academic.edu.vn</span>
                    </div>
                  </div>
                </div>

                {/* 2. Sĩ số lớp */}
                <div className="stat-card-metric-box">
                  <div className="metric-box-text">
                    <span className="metric-box-label">SĨ SỐ LỚP</span>
                    <span className="metric-box-value">
                      <strong>{selectedClass.currentStudents || 45}</strong> / {selectedClass.maxStudents || 45} HS
                    </span>
                  </div>
                  <div className="metric-box-icon purple">
                    <Users size={18} />
                  </div>
                </div>

                {/* 3. Điểm TB lớp */}
                <div className="stat-card-metric-box">
                  <div className="metric-box-text">
                    <span className="metric-box-label">ĐIỂM TB LỚP</span>
                    <span className="metric-box-value purple">
                      <strong>8.65</strong> / 10.0
                    </span>
                  </div>
                  <div className="metric-box-icon purple">
                    <Star size={18} />
                  </div>
                </div>

                {/* 4. Xếp loại HS */}
                <div className="stat-card-metric-box">
                  <div className="metric-box-text">
                    <span className="metric-box-label">XẾP LOẠI HS</span>
                    <span className="metric-box-value">
                      <strong>32 Giỏi</strong> • 13 Khá
                    </span>
                  </div>
                  <div className="metric-box-icon blue">
                    <PieChart size={18} />
                  </div>
                </div>
              </div>

              {/* Filter Row */}
              <div className="class-dialog-filter-bar">
                <div className="dialog-search-wrapper">
                  <Search size={15} className="dialog-search-icon" />
                  <input 
                    type="text" 
                    placeholder="Tìm theo tên học sinh, mã HS, phụ huynh, SĐT..." 
                    value={studentSearch}
                    onChange={e => setStudentSearch(e.target.value)}
                    className="dialog-search-input"
                  />
                  {studentSearch && (
                    <button type="button" onClick={() => setStudentSearch('')} className="dialog-search-clear">
                      <X size={13} />
                    </button>
                  )}
                </div>

                <div className="dialog-filters-group">
                  <div className="dialog-select-wrapper">
                    <select value={studentGenderFilter} onChange={e => setStudentGenderFilter(e.target.value)}>
                      <option value="all">Giới tính: Tất cả</option>
                      <option value="Nam">Nam</option>
                      <option value="Nữ">Nữ</option>
                    </select>
                    <ChevronDown size={13} className="select-arrow" />
                  </div>

                  <div className="dialog-select-wrapper">
                    <select value={studentAcademicFilter} onChange={e => setStudentAcademicFilter(e.target.value)}>
                      <option value="all">Học lực: Tất cả</option>
                      <option value="Xuất sắc">Xuất sắc</option>
                      <option value="Giỏi">Giỏi</option>
                      <option value="Khá">Khá</option>
                    </select>
                    <ChevronDown size={13} className="select-arrow" />
                  </div>

                  <button 
                    type="button" 
                    className="btn-dialog-sort"
                    onClick={() => setStudentSortBy(prev => prev === 'alphabet' ? 'gpa_desc' : 'alphabet')}
                  >
                    <ArrowUpDown size={14} />
                    <span>{studentSortBy === 'gpa_desc' ? 'Sắp xếp: Thứ hạng GPA' : 'Sắp xếp: Bảng chữ cái (A-Z)'}</span>
                  </button>
                </div>
              </div>

              {/* Student Table */}
              <div className="class-dialog-table-wrapper">
                <table className="class-dialog-table">
                  <thead>
                    <tr>
                      <th className="th-st-check">
                        <input 
                          type="checkbox" 
                          checked={filteredClassStudents.length > 0 && studentSelectedIds.length === filteredClassStudents.length}
                          onChange={handleSelectAllStudents}
                        />
                      </th>
                      <th className="th-st-stt">STT</th>
                      <th className="th-st-code">MÃ HS</th>
                      <th className="th-st-name">HỌ VÀ TÊN HỌC SINH</th>
                      <th className="th-st-birth">NGÀY SINH / GT</th>
                      <th className="th-st-parent">PHỤ HUYNH & SĐT LIÊN HỆ</th>
                      <th className="th-st-gpa text-center">GPA HỌC KỲ</th>
                      <th className="th-st-rank text-center">XẾP LOẠI</th>
                      <th className="th-st-actions text-center" style={{ width: '80px' }}>THAO TÁC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredClassStudents.length === 0 ? (
                      <tr>
                        <td colSpan="9" className="empty-students-cell">
                          Không tìm thấy học sinh nào phù hợp với bộ lọc hiện tại.
                        </td>
                      </tr>
                    ) : (
                      filteredClassStudents.map((st, index) => {
                        const isStSelected = studentSelectedIds.includes(st.id);
                        return (
                          <tr key={st.id} className={isStSelected ? 'student-row-selected' : ''}>
                            <td className="td-st-check">
                              <input 
                                type="checkbox" 
                                checked={isStSelected}
                                onChange={() => handleToggleSelectStudent(st.id)}
                              />
                            </td>
                            <td className="td-st-stt">{String(index + 1).padStart(2, '0')}</td>
                            <td className="td-st-code font-mono text-purple">{st.code}</td>
                            <td className="td-st-name">
                              <div className="student-profile-cell">
                                {st.avatarUrl ? (
                                  <img src={st.avatarUrl} alt="" className="student-avatar-img" />
                                ) : (
                                  <div 
                                    className="student-avatar-badge" 
                                    style={{ backgroundColor: st.avatarBg, color: st.avatarColor }}
                                  >
                                    {st.avatarText}
                                  </div>
                                )}
                                <div className="student-name-col">
                                  <span className="student-full-name">{st.name}</span>
                                  <span className="student-email-text">{st.email}</span>
                                </div>
                              </div>
                            </td>
                            <td className="td-st-birth">
                              <div className="birth-gender-col">
                                <span className="birth-val">{st.birthDate}</span>
                                <span className="gender-val">{st.gender}</span>
                              </div>
                            </td>
                            <td className="td-st-parent">
                              <div className="parent-contact-col">
                                <span className="parent-name-val">{st.parentName} ({st.parentRole})</span>
                                <span className="parent-phone-val">{st.parentPhone}</span>
                              </div>
                            </td>
                            <td className="td-st-gpa text-center">
                              <span className="gpa-score-text">{st.gpa.toFixed(1)}</span>
                            </td>
                            <td className="td-st-rank text-center">
                              <span className={`rank-pill-badge ${st.rank === 'Xuất sắc' ? 'excellent' : st.rank === 'Giỏi' ? 'good' : 'fair'}`}>
                                {st.rank}
                              </span>
                            </td>
                            <td className="td-st-actions text-center">
                              <button 
                                type="button" 
                                className="st-icon-btn edit-only" 
                                title="Chỉnh sửa thông tin học sinh"
                                onClick={() => handleOpenEditStudent(st)}
                              >
                                <Edit2 size={15} />
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer */}
            <div className="class-dialog-footer">
              <div className="dialog-footer-left">
                Hiển thị tất cả <strong>{filteredClassStudents.length}</strong> trong số <strong>{classStudents.length}</strong> học sinh
              </div>

              <div className="dialog-footer-right">
                <button 
                  type="button" 
                  className="btn-dialog-print"
                  onClick={() => showToast(`Đang chuẩn bị in bảng điểm lớp ${selectedClass.name}...`)}
                >
                  <Printer size={15} />
                  <span>In bảng điểm lớp</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Xuất dữ liệu Excel */}
      {isExportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsExportModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Xuất dữ liệu danh sách lớp học</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsExportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <p className="admin-modal-desc">
                Tải xuống danh sách toàn bộ {filteredClasses.length} lớp học cùng thông tin giáo viên chủ nhiệm tương ứng.
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tập tin</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input type="radio" name="classExportFormat" defaultChecked />
                    <span>Bảng tính Excel (.xlsx)</span>
                  </label>
                  <label className="export-option-box">
                    <input type="radio" name="classExportFormat" />
                    <span>Tài liệu PDF (.pdf)</span>
                  </label>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsExportModalOpen(false)}>
                  Hủy
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={() => {
                    setIsExportModalOpen(false);
                    showToast('Đang tạo và tải xuống tập tin danh sách lớp học...');
                  }}
                >
                  <Download size={16} />
                  <span>Tải xuống</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Thêm học sinh vào lớp */}
      {isAddStudentToClassModalOpen && selectedClass && (
        <div className="add-student-modal-backdrop" onClick={() => setIsAddStudentToClassModalOpen(false)}>
          <div className="add-student-modal-card" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="add-student-modal-header">
              <div className="add-student-title-block">
                <div className="add-student-icon-circle">
                  <UserPlus size={22} />
                </div>
                <div>
                  <h3 className="add-student-modal-title">
                    Thêm học sinh vào lớp: {selectedClass.name}
                  </h3>
                  <p className="add-student-modal-subtitle">
                    Phân bổ học sinh từ danh sách trường, tạo hồ sơ mới hoặc nhập hàng loạt từ file Excel.
                  </p>
                </div>
              </div>
              <button 
                type="button" 
                className="add-student-modal-close" 
                onClick={() => setIsAddStudentToClassModalOpen(false)}
                title="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            {/* Class Info Banner */}
            <div className="add-student-class-banner">
              <div className="banner-info-items">
                <span className="banner-chip-badge">{selectedClass.grade}</span>
                <span className="banner-text-item"><strong>Mã lớp:</strong> {selectedClass.code}</span>
                <span className="banner-text-divider">•</span>
                <span className="banner-text-item"><strong>GVCN:</strong> {selectedClass.teacher?.name || 'Chưa phân công'}</span>
              </div>
              <div className="banner-capacity-badge">
                <span>Sĩ số hiện tại: <strong>{classStudents.length} / {selectedClass.maxStudents || 45}</strong></span>
                <div className="capacity-mini-bar">
                  <div 
                    className="capacity-mini-fill" 
                    style={{ 
                      width: `${Math.min(100, Math.round((classStudents.length / (selectedClass.maxStudents || 45)) * 100))}%`,
                      backgroundColor: classStudents.length >= (selectedClass.maxStudents || 45) ? '#EF4444' : '#10B981'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Mode Tabs */}
            <div className="add-student-tabs-row">
              <button 
                type="button" 
                className={`add-student-tab-btn ${addStudentTab === 'select' ? 'active' : ''}`}
                onClick={() => setAddStudentTab('select')}
              >
                <Users size={16} />
                <span>Chọn từ danh sách trường</span>
                <span className="tab-counter-badge">{availableCandidates.length}</span>
              </button>

              <button 
                type="button" 
                className={`add-student-tab-btn ${addStudentTab === 'create' ? 'active' : ''}`}
                onClick={() => setAddStudentTab('create')}
              >
                <UserPlus size={16} />
                <span>Tạo hồ sơ mới</span>
              </button>

              <button 
                type="button" 
                className={`add-student-tab-btn ${addStudentTab === 'excel' ? 'active' : ''}`}
                onClick={() => setAddStudentTab('excel')}
              >
                <FileSpreadsheet size={16} />
                <span>Nhập từ file Excel / CSV</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="add-student-modal-body">
              {/* TAB 1: Chọn từ danh sách trường */}
              {addStudentTab === 'select' && (
                <div className="tab-pane-select">
                  {/* Thanh Filter Phân Loại Khối Lớp */}
                  <div className="candidate-grade-filter-bar">
                    <div className="candidate-grade-tabs">
                      {[
                        { key: 'all', label: 'Tất cả khối' },
                        { key: 'Khối 10', label: 'Khối 10' },
                        { key: 'Khối 11', label: 'Khối 11' },
                        { key: 'Khối 12', label: 'Khối 12' }
                      ].map(g => {
                        const count = g.key === 'all' 
                          ? availableCandidates.length 
                          : availableCandidates.filter(c => c.currentGrade === g.key).length;
                        return (
                          <button
                            key={g.key}
                            type="button"
                            className={`candidate-grade-tab-pill ${candidateGradeFilter === g.key ? 'active' : ''}`}
                            onClick={() => setCandidateGradeFilter(g.key)}
                          >
                            <span>{g.label}</span>
                            <span className="grade-count-chip">{count}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Filters bar */}
                  <div className="candidate-filter-bar">
                    <div className="candidate-search-wrapper">
                      <Search size={15} className="candidate-search-icon" />
                      <input 
                        type="text" 
                        placeholder="Tìm theo họ tên, mã HS, SĐT phụ huynh..." 
                        value={candidateSearch}
                        onChange={e => setCandidateSearch(e.target.value)}
                        className="candidate-search-input"
                      />
                      {candidateSearch && (
                        <button type="button" onClick={() => setCandidateSearch('')} className="candidate-search-clear">
                          <X size={13} />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Selection Status Row */}
                  <div className="candidate-selection-row">
                    <label className="candidate-select-all-label">
                      <input 
                        type="checkbox" 
                        checked={filteredCandidates.length > 0 && selectedCandidateIds.length === filteredCandidates.length}
                        onChange={handleSelectAllCandidates}
                      />
                      <span>Chọn tất cả ({filteredCandidates.length} học sinh)</span>
                    </label>
                    <span className="candidate-selected-badge">
                      Đã chọn: <strong>{selectedCandidateIds.length}</strong> học sinh
                    </span>
                  </div>

                  {/* Candidate List Table */}
                  <div className="candidate-table-wrapper">
                    <table className="candidate-table">
                      <thead>
                        <tr>
                          <th className="th-cand-check">#</th>
                          <th className="th-cand-code">MÃ HS</th>
                          <th className="th-cand-name">HỌ VÀ TÊN HỌC SINH</th>
                          <th className="th-cand-birth">NGÀY SINH / GT</th>
                          <th className="th-cand-parent">PHỤ HUYNH & SĐT</th>
                          <th className="th-cand-grade text-center">KHỐI LỚP</th>
                          <th className="th-cand-gpa text-center">GPA</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredCandidates.length === 0 ? (
                          <tr>
                            <td colSpan="7" className="empty-candidate-cell">
                              <AlertCircle size={20} className="empty-icon" />
                              <span>Không tìm thấy học sinh nào phù hợp với bộ lọc.</span>
                            </td>
                          </tr>
                        ) : (
                          filteredCandidates.map(cand => {
                            const isSelected = selectedCandidateIds.includes(cand.id);
                            return (
                              <tr 
                                key={cand.id} 
                                className={`candidate-row ${isSelected ? 'row-active' : ''}`}
                                onClick={() => handleToggleSelectCandidate(cand.id)}
                              >
                                <td className="td-cand-check" onClick={e => e.stopPropagation()}>
                                  <input 
                                    type="checkbox" 
                                    checked={isSelected}
                                    onChange={() => handleToggleSelectCandidate(cand.id)}
                                  />
                                </td>
                                <td className="td-cand-code font-mono text-purple">{cand.code}</td>
                                <td className="td-cand-name">
                                  <div className="candidate-name-cell">
                                    <div 
                                      className="candidate-avatar-badge" 
                                      style={{ backgroundColor: cand.avatarBg, color: cand.avatarColor }}
                                    >
                                      {cand.avatarText}
                                    </div>
                                    <div className="candidate-name-info">
                                      <span className="candidate-full-name">{cand.name}</span>
                                      <span className="candidate-email">{cand.email}</span>
                                    </div>
                                  </div>
                                </td>
                                <td className="td-cand-birth">
                                  <div className="birth-gender-col">
                                    <span className="birth-val">{cand.birthDate}</span>
                                    <span className="gender-val">{cand.gender}</span>
                                  </div>
                                </td>
                                <td className="td-cand-parent">
                                  <div className="parent-contact-col">
                                    <span className="parent-name-val">{cand.parentName} ({cand.parentRole})</span>
                                    <span className="parent-phone-val">{cand.parentPhone}</span>
                                  </div>
                                </td>
                                <td className="td-cand-grade text-center">
                                  <span className="candidate-grade-badge">
                                    {cand.currentGrade}
                                  </span>
                                </td>
                                <td className="td-cand-gpa text-center">
                                  <span className="gpa-score-text">{cand.gpa.toFixed(1)}</span>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 2: Tạo hồ sơ học sinh mới */}
              {addStudentTab === 'create' && (
                <form id="createStudentForm" onSubmit={handleCreateAndAddStudent} className="tab-pane-create">
                  <div className="create-student-grid">
                    {/* Row 1 */}
                    <div className="form-field-group">
                      <label className="field-label">Mã học sinh</label>
                      <input 
                        type="text" 
                        placeholder="Để trống để tự động sinh mã (VD: HS2024146)"
                        value={newStudentForm.code}
                        onChange={e => setNewStudentForm({ ...newStudentForm, code: e.target.value })}
                        className="field-input font-mono"
                      />
                    </div>

                    <div className="form-field-group">
                      <label className="field-label">Họ và tên học sinh <span className="text-red">*</span></label>
                      <input 
                        type="text" 
                        required
                        placeholder="VD: Trần Quốc Toản"
                        value={newStudentForm.name}
                        onChange={e => setNewStudentForm({ ...newStudentForm, name: e.target.value })}
                        className="field-input"
                      />
                    </div>

                    {/* Row 2 */}
                    <div className="form-field-group">
                      <label className="field-label">Ngày sinh <span className="text-red">*</span></label>
                      <input 
                        type="date" 
                        required
                        value={newStudentForm.birthDate}
                        onChange={e => setNewStudentForm({ ...newStudentForm, birthDate: e.target.value })}
                        className="field-input"
                      />
                    </div>

                    <div className="form-field-group">
                      <label className="field-label">Giới tính <span className="text-red">*</span></label>
                      <select 
                        value={newStudentForm.gender}
                        onChange={e => setNewStudentForm({ ...newStudentForm, gender: e.target.value })}
                        className="field-select"
                      >
                        <option value="Nam">Nam</option>
                        <option value="Nữ">Nữ</option>
                      </select>
                    </div>

                    {/* Row 3 */}
                    <div className="form-field-group">
                      <label className="field-label">Email học sinh</label>
                      <input 
                        type="email" 
                        placeholder="VD: quoctoan.12a1@academic.edu.vn"
                        value={newStudentForm.email}
                        onChange={e => setNewStudentForm({ ...newStudentForm, email: e.target.value })}
                        className="field-input"
                      />
                    </div>

                    <div className="form-field-group">
                      <label className="field-label">Số điện thoại học sinh</label>
                      <input 
                        type="tel" 
                        placeholder="VD: 0912.345.678"
                        value={newStudentForm.phone}
                        onChange={e => setNewStudentForm({ ...newStudentForm, phone: e.target.value })}
                        className="field-input"
                      />
                    </div>

                    {/* Row 4 */}
                    <div className="form-field-group">
                      <label className="field-label">Họ tên phụ huynh <span className="text-red">*</span></label>
                      <input 
                        type="text" 
                        required
                        placeholder="VD: Trần Văn Hải"
                        value={newStudentForm.parentName}
                        onChange={e => setNewStudentForm({ ...newStudentForm, parentName: e.target.value })}
                        className="field-input"
                      />
                    </div>

                    <div className="form-field-row-split">
                      <div className="form-field-group flex-1">
                        <label className="field-label">Mối quan hệ</label>
                        <select 
                          value={newStudentForm.parentRole}
                          onChange={e => setNewStudentForm({ ...newStudentForm, parentRole: e.target.value })}
                          className="field-select"
                        >
                          <option value="Bố">Bố</option>
                          <option value="Mẹ">Mẹ</option>
                          <option value="Giám hộ">Người giám hộ</option>
                        </select>
                      </div>

                      <div className="form-field-group flex-2">
                        <label className="field-label">SĐT phụ huynh <span className="text-red">*</span></label>
                        <input 
                          type="tel" 
                          required
                          placeholder="VD: 0983.112.445"
                          value={newStudentForm.parentPhone}
                          onChange={e => setNewStudentForm({ ...newStudentForm, parentPhone: e.target.value })}
                          className="field-input"
                        />
                      </div>
                    </div>

                    {/* Row 5 */}
                    <div className="form-field-group col-span-2">
                      <label className="field-label">Địa chỉ thường trú</label>
                      <input 
                        type="text" 
                        placeholder="VD: Số 24, Phố Bà Triệu, Phường Hàng Bài, Quận Hoàn Kiếm, Hà Nội"
                        value={newStudentForm.address}
                        onChange={e => setNewStudentForm({ ...newStudentForm, address: e.target.value })}
                        className="field-input"
                      />
                    </div>
                  </div>
                </form>
              )}

              {/* TAB 3: Nhập từ file Excel */}
              {addStudentTab === 'excel' && (
                <div className="tab-pane-excel">
                  <div className="excel-upload-dropzone">
                    <Upload size={38} className="dropzone-upload-icon" />
                    <h4>Tải lên tập tin danh sách học sinh</h4>
                    <p>Kéo và thả file danh sách học sinh vào đây hoặc nhấn để chọn từ máy tính.</p>
                    <span className="dropzone-subtext">Hỗ trợ định dạng: .xlsx, .xls, .csv (Tối đa 10MB)</span>
                    
                    <label className="btn-browse-file">
                      <input 
                        type="file" 
                        accept=".xlsx,.xls,.csv" 
                        style={{ display: 'none' }}
                        onChange={e => {
                          if (e.target.files && e.target.files[0]) {
                            setUploadedFileName(e.target.files[0].name);
                          }
                        }}
                      />
                      <span>Chọn tập tin từ máy</span>
                    </label>

                    {uploadedFileName && (
                      <div className="uploaded-file-tag">
                        <FileSpreadsheet size={16} />
                        <span>{uploadedFileName}</span>
                        <button type="button" onClick={() => setUploadedFileName('')}>
                          <X size={14} />
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="excel-template-guide-box">
                    <div className="guide-box-left">
                      <Info size={20} className="guide-icon" />
                      <div>
                        <h5>Quy chuẩn tập tin mẫu:</h5>
                        <p>Tập tin cần chứa các cột: <strong>Mã HS, Họ và tên, Ngày sinh, Giới tính, Họ tên phụ huynh, SĐT phụ huynh</strong>.</p>
                      </div>
                    </div>
                    <button 
                      type="button" 
                      className="btn-download-template"
                      onClick={() => showToast('Đang tải xuống file mẫu template_danh_sach_hoc_sinh.xlsx...')}
                    >
                      <Download size={14} />
                      <span>Tải file mẫu Excel (.xlsx)</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="add-student-modal-footer">
              <button 
                type="button" 
                className="btn-add-student-cancel" 
                onClick={() => setIsAddStudentToClassModalOpen(false)}
              >
                Hủy bỏ
              </button>

              {addStudentTab === 'select' && (
                <button 
                  type="button" 
                  className="btn-add-student-submit"
                  disabled={selectedCandidateIds.length === 0}
                  onClick={handleAddCandidatesToClass}
                >
                  <UserPlus size={16} />
                  <span>
                    {selectedCandidateIds.length === 0 
                      ? 'Chọn học sinh để thêm' 
                      : `Thêm ${selectedCandidateIds.length} học sinh vào lớp`}
                  </span>
                </button>
              )}

              {addStudentTab === 'create' && (
                <button 
                  type="submit" 
                  form="createStudentForm"
                  className="btn-add-student-submit"
                >
                  <CheckCircle2 size={16} />
                  <span>Tạo & Thêm vào lớp</span>
                </button>
              )}

              {addStudentTab === 'excel' && (
                <button 
                  type="button" 
                  className="btn-add-student-submit"
                  disabled={!uploadedFileName}
                  onClick={handleImportExcelStudents}
                >
                  <FileSpreadsheet size={16} />
                  <span>Nhập danh sách vào lớp</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Chỉnh sửa thông tin học sinh */}
      {isEditStudentModalOpen && editingStudent && (
        <div className="add-student-modal-backdrop" style={{ zIndex: 1150 }} onClick={() => setIsEditStudentModalOpen(false)}>
          <div className="add-student-modal-card" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}>
            <div className="add-student-modal-header">
              <div className="add-student-title-block">
                <div className="add-student-icon-circle">
                  <Edit2 size={20} />
                </div>
                <div>
                  <h3 className="add-student-modal-title">
                    Chỉnh sửa thông tin học sinh
                  </h3>
                  <p className="add-student-modal-subtitle">
                    Cập nhật hồ sơ học sinh <strong>{editingStudent.name}</strong> ({editingStudent.code})
                  </p>
                </div>
              </div>
              <button 
                type="button" 
                className="add-student-modal-close" 
                onClick={() => setIsEditStudentModalOpen(false)}
                title="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveEditStudent}>
              <div className="create-student-grid" style={{ padding: '20px 24px' }}>
                <div className="form-field-group">
                  <label className="field-label">Mã học sinh</label>
                  <input 
                    type="text" 
                    value={editStudentForm.code} 
                    disabled 
                    className="field-input font-mono" 
                    style={{ backgroundColor: '#F8F6FC', color: '#6D28D9', cursor: 'not-allowed' }}
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Họ và tên <span className="text-red">*</span></label>
                  <input 
                    type="text" 
                    required 
                    value={editStudentForm.name} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, name: e.target.value })}
                    className="field-input"
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Ngày sinh</label>
                  <input 
                    type="text" 
                    placeholder="DD/MM/YYYY"
                    value={editStudentForm.birthDate} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, birthDate: e.target.value })}
                    className="field-input"
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Giới tính</label>
                  <select 
                    value={editStudentForm.gender} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, gender: e.target.value })}
                    className="field-select"
                  >
                    <option value="Nam">Nam</option>
                    <option value="Nữ">Nữ</option>
                  </select>
                </div>

                <div className="form-field-group col-span-2">
                  <label className="field-label">Email học sinh</label>
                  <input 
                    type="email" 
                    value={editStudentForm.email} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, email: e.target.value })}
                    className="field-input"
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Phụ huynh học sinh</label>
                  <input 
                    type="text" 
                    value={editStudentForm.parentName} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, parentName: e.target.value })}
                    className="field-input"
                  />
                </div>

                <div className="form-field-row-split">
                  <div className="form-field-group flex-1">
                    <label className="field-label">Mối quan hệ</label>
                    <select 
                      value={editStudentForm.parentRole} 
                      onChange={e => setEditStudentForm({ ...editStudentForm, parentRole: e.target.value })}
                      className="field-select"
                    >
                      <option value="Bố">Bố</option>
                      <option value="Mẹ">Mẹ</option>
                      <option value="Giám hộ">Giám hộ</option>
                    </select>
                  </div>
                  <div className="form-field-group flex-2">
                    <label className="field-label">SĐT phụ huynh <span className="text-red">*</span></label>
                    <input 
                      type="tel" 
                      required 
                      value={editStudentForm.parentPhone} 
                      onChange={e => setEditStudentForm({ ...editStudentForm, parentPhone: e.target.value })}
                      className="field-input"
                    />
                  </div>
                </div>

                <div className="form-field-group">
                  <label className="field-label">Điểm GPA học kỳ</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="10" 
                    value={editStudentForm.gpa} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, gpa: e.target.value })}
                    className="field-input font-bold"
                  />
                </div>

                <div className="form-field-group">
                  <label className="field-label">Xếp loại học lực</label>
                  <select 
                    value={editStudentForm.rank} 
                    onChange={e => setEditStudentForm({ ...editStudentForm, rank: e.target.value })}
                    className="field-select"
                  >
                    <option value="Xuất sắc">Xuất sắc</option>
                    <option value="Giỏi">Giỏi</option>
                    <option value="Khá">Khá</option>
                    <option value="Trung bình">Trung bình</option>
                  </select>
                </div>
              </div>

              <div className="add-student-modal-footer">
                <button 
                  type="button" 
                  className="btn-add-student-cancel" 
                  onClick={() => setIsEditStudentModalOpen(false)}
                >
                  Hủy
                </button>
                <button 
                  type="submit" 
                  className="btn-add-student-submit"
                >
                  <CheckCircle2 size={16} />
                  <span>Lưu thay đổi</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
