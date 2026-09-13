// File Name: StudentExerciseTakingPage.jsx
// Description: Interactive student examination interface supporting 3 question types: Multiple Choice (4 options), True/False (4 sub-items), and Short Answer (with on-screen numpad helper).
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
  HelpCircle, 
  Settings, 
  Flag, 
  ArrowLeft, 
  ArrowRight, 
  Send, 
  CheckCircle2, 
  XCircle, 
  Hash, 
  Delete, 
  RotateCcw, 
  Sparkles, 
  Info,
  AlertCircle,
  X,
  ShieldAlert,
  Eye,
  Lock
} from 'lucide-react';
import { useNavigate, Link, useParams } from 'react-router-dom';
import './StudentExerciseTakingPage.css';

export default function StudentExerciseTakingPage() {
  const navigate = useNavigate();
  const { exerciseId } = useParams();
  const currentExamId = exerciseId || '1';

  // Exercise / Exam Metadata
  const savedAiExercise = useMemo(() => {
    try {
      const saved = localStorage.getItem('tk_student_ai_exercises');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.find(ex => String(ex.id) === String(currentExamId));
        }
      }
    } catch (e) {
      console.error(e);
    }
    return null;
  }, [currentExamId]);

  const isChemistry = currentExamId === '4' || Boolean(savedAiExercise && savedAiExercise.subject === 'Hóa học');
  const isAiExercise = Boolean(savedAiExercise);

  const exerciseInfo = useMemo(() => {
    if (savedAiExercise) {
      const p1 = savedAiExercise.part1Count || 15;
      const p2 = savedAiExercise.part2Count || 5;
      const p3 = savedAiExercise.part3Count || 5;
      return {
        id: savedAiExercise.id,
        title: savedAiExercise.title || 'Bài tập tạo sinh AI',
        subject: savedAiExercise.subject || 'Hóa học',
        category: 'exercise',
        categoryLabel: 'Bài tập tạo sinh AI',
        teacher: savedAiExercise.teacher || 'Trợ lý AI Tam Khang',
        totalQuestions: savedAiExercise.totalQuestions || (p1 + p2 + p3),
        part1Count: p1,
        part2Count: p2,
        part3Count: p3,
        durationMinutes: savedAiExercise.durationMinutes || 45,
        isExam: false,
        isAiGenerated: true
      };
    }

    if (isChemistry) {
      return {
        id: 4,
        title: 'Hóa học 12 – Chuyên đề Este & Lipit',
        subject: 'Hóa học',
        category: 'exercise',
        categoryLabel: 'Bài tập rèn luyện',
        teacher: 'Trần Thị Mai',
        totalQuestions: 35,
        part1Count: 15,
        part2Count: 10,
        part3Count: 10,
        durationMinutes: 50,
        isExam: false
      };
    }

    return {
      id: 1,
      title: 'Đề thi khảo sát chất lượng - Môn Toán (THPT 2025)',
      subject: 'Toán học',
      category: 'exam',
      categoryLabel: 'Bài thi chính thức',
      teacher: 'Trần Văn B',
      totalQuestions: 40,
      part1Count: 15,
      part2Count: 15,
      part3Count: 10,
      durationMinutes: 45,
      isExam: true
    };
  }, [savedAiExercise, isChemistry]);

  const totalQuestions = exerciseInfo.totalQuestions;

  // Active question index (0-indexed, default is Question 1)
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  
  // Dynamic answers dictionary
  const [answers, setAnswers] = useState(
    isChemistry 
      ? { 0: 'A', 1: 'A', 2: 'A', 3: 'A', 15: { a: true, b: false, c: true, d: false } }
      : {
          0: 'A', 1: 'B', 2: 'C', 3: 'A', 4: 'B',
          5: 'C', 6: 'D', 7: 'A', 8: 'B', 9: 'C',
          10: 'D', 11: 'A', 12: 'B', 13: 'C', 14: 'D',
          15: { a: true, b: true, c: false, d: true },
          22: { a: true, b: false }
        }
  );

  const [flaggedQuestions, setFlaggedQuestions] = useState(isChemistry ? { 15: true } : { 15: true });
  const [timeLeft, setTimeLeft] = useState(exerciseInfo.durationMinutes * 60 + 12);
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'flagged'

  // Submission & Exam Lock States
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isReadOnlyReview, setIsReadOnlyReview] = useState(false);
  
  // Check if exam/exercise is already submitted in localStorage
  const savedSubmission = useMemo(() => {
    try {
      const data = localStorage.getItem(`tk_exam_submitted_${currentExamId}`);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  }, [currentExamId]);

  const [isExamSubmitted, setIsExamSubmitted] = useState(Boolean(savedSubmission));
  const [submissionResult, setSubmissionResult] = useState(savedSubmission);

  // Timer countdown (only active when exam is not submitted)
  useEffect(() => {
    if (isExamSubmitted) return;
    const timer = setInterval(() => {
      setTimeLeft(prev => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [isExamSubmitted]);

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Toggle flag for current question
  const toggleFlag = (index) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setFlaggedQuestions(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Handler for Multiple Choice 4 options
  const handleSelectOption = (qIdx, optionKey) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setAnswers(prev => ({
      ...prev,
      [qIdx]: optionKey
    }));
  };

  // Handler for True/False sub-item
  const handleSelectTrueFalse = (qIdx, subKey, boolVal) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setAnswers(prev => {
      const currentTF = prev[qIdx] && typeof prev[qIdx] === 'object' ? prev[qIdx] : {};
      return {
        ...prev,
        [qIdx]: {
          ...currentTF,
          [subKey]: boolVal
        }
      };
    });
  };

  // Clean and validate Short Answer (Max 4 chars, decimal comma only)
  const cleanShortAnswer = (val) => {
    if (!val) return '';
    // Auto-convert dot to comma
    let formatted = String(val).replace(/\./g, ',');
    // Allow only digits, leading minus, and comma
    formatted = formatted.replace(/[^0-9,-]/g, '');

    // Ensure minus is only at index 0
    const isNegative = formatted.startsWith('-');
    formatted = formatted.replace(/-/g, '');
    if (isNegative) {
      formatted = '-' + formatted;
    }

    // Ensure only one comma
    const commaIndex = formatted.indexOf(',');
    if (commaIndex !== -1) {
      formatted = formatted.substring(0, commaIndex + 1) + formatted.substring(commaIndex + 1).replace(/,/g, '');
    }

    // Strict 4 characters maximum
    return formatted.slice(0, 4);
  };

  // Handler for Short Answer text
  const handleShortAnswerChange = (qIdx, textVal) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    const cleaned = cleanShortAnswer(textVal);
    setAnswers(prev => ({
      ...prev,
      [qIdx]: cleaned
    }));
  };

  // Numpad button click for Short Answer
  const handleNumpadPress = (char) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    const currentVal = typeof answers[currentQuestionIdx] === 'string' ? answers[currentQuestionIdx] : '';
    
    if (char === 'CLEAR') {
      handleShortAnswerChange(currentQuestionIdx, '');
    } else if (char === 'BACKSPACE') {
      handleShortAnswerChange(currentQuestionIdx, currentVal.slice(0, -1));
    } else if (char === '-') {
      if (currentVal.startsWith('-')) {
        return;
      }
      if (currentVal === '') {
        handleShortAnswerChange(currentQuestionIdx, '-');
      } else if (currentVal.length < 4) {
        handleShortAnswerChange(currentQuestionIdx, '-' + currentVal);
      }
    } else if (char === '+') {
      if (currentVal.startsWith('-')) {
        handleShortAnswerChange(currentQuestionIdx, currentVal.substring(1));
      }
    } else if (char === ',') {
      if (!currentVal.includes(',') && currentVal.length < 4) {
        if (currentVal === '' || currentVal === '-') {
          handleShortAnswerChange(currentQuestionIdx, currentVal + '0,');
        } else {
          handleShortAnswerChange(currentQuestionIdx, currentVal + ',');
        }
      }
    } else {
      if (currentVal.length < 4) {
        handleShortAnswerChange(currentQuestionIdx, currentVal + char);
      }
    }
  };

  const handleNext = () => {
    if (currentQuestionIdx < totalQuestions - 1) {
      setCurrentQuestionIdx(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentQuestionIdx > 0) {
      setCurrentQuestionIdx(prev => prev - 1);
    }
  };

  // Check if a question is answered
  const isQuestionAnswered = (qIdx) => {
    const ans = answers[qIdx];
    if (ans === undefined || ans === null) return false;
    if (typeof ans === 'string') return ans.trim().length > 0;
    if (typeof ans === 'object') return Object.keys(ans).length > 0;
    return false;
  };

  const answeredCount = Object.keys(answers).filter(k => isQuestionAnswered(Number(k)) && Number(k) < totalQuestions).length;
  const unansweredCount = totalQuestions - answeredCount;
  const flaggedCount = Object.keys(flaggedQuestions).filter(k => flaggedQuestions[k] && Number(k) < totalQuestions).length;
  const progressPercent = Math.round((answeredCount / totalQuestions) * 100);

  // Breakdown by Part
  const part1Answered = Array.from({ length: exerciseInfo.part1Count }, (_, i) => i).filter(i => isQuestionAnswered(i)).length;
  const part2Answered = Array.from({ length: exerciseInfo.part2Count }, (_, i) => i + exerciseInfo.part1Count).filter(i => isQuestionAnswered(i)).length;
  const part3Answered = Array.from({ length: exerciseInfo.part3Count }, (_, i) => i + exerciseInfo.part1Count + exerciseInfo.part2Count).filter(i => isQuestionAnswered(i)).length;

  // Open modal confirmation
  const handleOpenSubmitModal = () => {
    if (isExamSubmitted) return;
    setIsSubmitModalOpen(true);
  };

  // Confirm final submission
  const handleConfirmSubmit = () => {
    const calculatedScore = ((answeredCount / totalQuestions) * 10).toFixed(2);
    const resultData = {
      submittedAt: new Date().toISOString(),
      formattedTime: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' · ' + new Date().toLocaleDateString('vi-VN'),
      answeredCount,
      unansweredCount,
      flaggedCount,
      totalQuestions,
      score: calculatedScore,
      isExam: exerciseInfo.isExam,
      title: exerciseInfo.title
    };

    try {
      localStorage.setItem(`tk_exam_submitted_${currentExamId}`, JSON.stringify(resultData));
    } catch (e) {
      console.error('Failed to save state', e);
    }

    setSubmissionResult(resultData);
    setIsExamSubmitted(true);
    setIsSubmitModalOpen(false);
  };

  // Allow retake for practice exercises (category === 'exercise')
  const handleRetakeExercise = () => {
    try {
      localStorage.removeItem(`tk_exam_submitted_${currentExamId}`);
    } catch (e) {
      console.error('Failed to remove state', e);
    }
    setAnswers({});
    setFlaggedQuestions({});
    setTimeLeft(exerciseInfo.durationMinutes * 60);
    setIsExamSubmitted(false);
    setIsReadOnlyReview(false);
    setSubmissionResult(null);
    setCurrentQuestionIdx(0);
  };

  // Question Dataset (Dynamic for Chemistry vs Math)
  const questionData = useMemo(() => {
    const qNum = currentQuestionIdx + 1;

    // CHEMISTRY 12 DATASET (Este & Lipit)
    if (isChemistry) {
      // Chemistry Part I: Trắc nghiệm 4 lựa chọn (1 - 15)
      if (currentQuestionIdx < 15) {
        const chemPart1 = [
          {
            title: 'Công thức tổng quát của este no, đơn chức, mạch hở là:',
            options: [
              { key: 'A', text: 'CnH2nO2 (n ≥ 2)' },
              { key: 'B', text: 'CnH2n+2O2 (n ≥ 1)' },
              { key: 'C', text: 'CnH2n-2O2 (n ≥ 3)' },
              { key: 'D', text: 'CnH2nO (n ≥ 2)' }
            ]
          },
          {
            title: 'Thủy phân etyl fomat (HCOOC2H5) trong dung dịch NaOH đun nóng thu được muối nào sau đây?',
            options: [
              { key: 'A', text: 'HCOONa' },
              { key: 'B', text: 'CH3COONa' },
              { key: 'C', text: 'C2H5COONa' },
              { key: 'D', text: 'CH3ONa' }
            ]
          },
          {
            title: 'Chất béo tristearin có công thức cấu tạo thu gọn là:',
            options: [
              { key: 'A', text: '(C17H35COO)3C3H5' },
              { key: 'B', text: '(C17H33COO)3C3H5' },
              { key: 'C', text: '(C15H31COO)3C3H5' },
              { key: 'D', text: '(C17H31COO)3C3H5' }
            ]
          },
          {
            title: 'Este nào sau đây có mùi thơm đặc trưng của quả chuối chín?',
            options: [
              { key: 'A', text: 'Isoamyl axetat' },
              { key: 'B', text: 'Etyl butirat' },
              { key: 'C', text: 'Benzyl axetat' },
              { key: 'D', text: 'Geranyl axetat' }
            ]
          },
          {
            title: 'Cho 8,8 gam etyl axetat (CH3COOC2H5) phản ứng hoàn toàn với dung dịch NaOH vừa đủ, đun nóng. Khối lượng muối natri axetat (CH3COONa) thu được là:',
            options: [
              { key: 'A', text: '8,2 gam' },
              { key: 'B', text: '6,8 gam' },
              { key: 'C', text: '16,4 gam' },
              { key: 'D', text: '10,2 gam' }
            ]
          },
          {
            title: 'Phản ứng giữa axit cacboxylic và ancol có xúc tác H2SO4 đặc, đun nóng được gọi là phản ứng:',
            options: [
              { key: 'A', text: 'Este hóa' },
              { key: 'B', text: 'Xà phòng hóa' },
              { key: 'C', text: 'Trùng hợp' },
              { key: 'D', text: 'Thủy phân kiềm' }
            ]
          },
          {
            title: 'Số đồng phân este đơn chức ứng với công thức phân tử C3H6O2 là:',
            options: [
              { key: 'A', text: '2 đồng phân' },
              { key: 'B', text: '3 đồng phân' },
              { key: 'C', text: '4 đồng phân' },
              { key: 'D', text: '1 đồng phân' }
            ]
          },
          {
            title: 'Chất béo nào sau đây ở trạng thái lỏng ở nhiệt độ phòng (25°C)?',
            options: [
              { key: 'A', text: 'Triolein' },
              { key: 'B', text: 'Tristearin' },
              { key: 'C', text: 'Tripanmitin' },
              { key: 'D', text: 'Axit stearic' }
            ]
          },
          {
            title: 'Thủy phân chất béo trong dung dịch kiềm (NaOH hoặc KOH) luôn thu được sản phẩm là muối của axit béo và:',
            options: [
              { key: 'A', text: 'Glixerol' },
              { key: 'B', text: 'Etylen glicol' },
              { key: 'C', text: 'Ancol etylic' },
              { key: 'D', text: 'Ancol metylic' }
            ]
          },
          {
            title: 'Vinyl axetat (CH3COOCH=CH2) được điều chế trực tiếp từ phản ứng giữa axit axetic và:',
            options: [
              { key: 'A', text: 'Axetilen (C2H2)' },
              { key: 'B', text: 'Etilen (C2H4)' },
              { key: 'C', text: 'Ancol vinylic' },
              { key: 'D', text: 'Ancol etylic' }
            ]
          },
          {
            title: 'Đốt cháy hoàn toàn 1 mol este no, đơn chức, mạch hở thu được tỉ lệ mol CO2 và H2O là:',
            options: [
              { key: 'A', text: 'nCO2 : nH2O = 1 : 1' },
              { key: 'B', text: 'nCO2 : nH2O = 2 : 1' },
              { key: 'C', text: 'nCO2 > nH2O' },
              { key: 'D', text: 'nCO2 < nH2O' }
            ]
          },
          {
            title: 'Dầu mỡ động thực vật để lâu ngày trong không khí thường bị ôi thiu do:',
            options: [
              { key: 'A', text: 'Gốc axit béo không no bị oxi hóa chậm bởi không khí tạo peoxit' },
              { key: 'B', text: 'Este bị thủy phân hoàn toàn thành axit fomic' },
              { key: 'C', text: 'Glixerol bị bay hơi hết' },
              { key: 'D', text: 'Chất béo bị trùng hợp thành nhựa' }
            ]
          },
          {
            title: 'Xà phòng hóa hoàn toàn 1 mol tripanmitin (C15H31COO)3C3H5 cần vừa đủ bao nhiêu mol NaOH?',
            options: [
              { key: 'A', text: '3 mol' },
              { key: 'B', text: '1 mol' },
              { key: 'C', text: '2 mol' },
              { key: 'D', text: '6 mol' }
            ]
          },
          {
            title: 'Chất nào sau đây có nhiệt độ sôi thấp nhất trong các chất có cùng số nguyên tử C?',
            options: [
              { key: 'A', text: 'Etyl fomat (HCOOC2H5)' },
              { key: 'B', text: 'Axit propionic (C2H5COOH)' },
              { key: 'C', text: 'Ancol propylic (C3H7OH)' },
              { key: 'D', text: 'Propylamin (C3H7NH2)' }
            ]
          },
          {
            title: 'Metyl metacrylat (CH2=C(CH3)COOCH3) là monome dùng để trùng hợp tạo ra:',
            options: [
              { key: 'A', text: 'Thủy tinh hữu cơ plexiglas' },
              { key: 'B', text: 'Cao su buna' },
              { key: 'C', text: 'Nilon-6,6' },
              { key: 'D', text: 'Tơ lapsan' }
            ]
          }
        ];

        const q = chemPart1[currentQuestionIdx % chemPart1.length];
        return {
          part: 'Phần I: Trắc nghiệm 4 lựa chọn',
          number: qNum,
          type: 'single_choice',
          statement: q.title,
          options: q.options
        };
      }

      // Chemistry / AI Part II: Trắc nghiệm Đúng/Sai
      if (currentQuestionIdx >= exerciseInfo.part1Count && currentQuestionIdx < exerciseInfo.part1Count + exerciseInfo.part2Count) {
        const chemPart2 = [
          {
            statement: 'Xét các phát biểu sau về tính chất của este và lipit:',
            items: [
              { key: 'a', text: 'Các este thường nhẹ hơn nước, ít tan trong nước và có mùi thơm hoa quả đặc trưng.' },
              { key: 'b', text: 'Phản ứng thủy phân este trong môi trường kiềm (xà phòng hóa) là phản ứng thuận nghịch.' },
              { key: 'c', text: 'Etyl fomat có khả năng tham gia phản ứng tráng gương tạo bạc kim loại Ag.' },
              { key: 'd', text: 'Nhiệt độ sôi của este cao hơn nhiệt độ sôi của axit cacboxylic có cùng khối lượng phân tử.' }
            ]
          },
          {
            statement: 'Cho các phát biểu về chất béo và lipit:',
            items: [
              { key: 'a', text: 'Chất béo là trieste của glixerol với các axit béo monocacboxylic mạch cacbon dài, không phân nhánh.' },
              { key: 'b', text: 'Triolein có công thức (C17H33COO)3C3H5 tồn tại ở trạng thái lỏng ở nhiệt độ thường.' },
              { key: 'c', text: 'Hiđro hóa hoàn toàn chất béo lỏng (xúc tác Ni, đun nóng) thu được chất béo rắn sản xuất bơ nhân tạo.' },
              { key: 'd', text: 'Dầu thực vật và dầu mỡ bôi trơn máy móc đều có bản chất hóa học là este của axit béo.' }
            ]
          },
          {
            statement: 'Tiến hành thí nghiệm điều chế etyl axetat trong phòng thí nghiệm:',
            items: [
              { key: 'a', text: 'Hỗn hợp phản ứng gồm ancol etylic nguyên chất, axit axetic nguyên chất và vài giọt H2SO4 đặc.' },
              { key: 'b', text: 'Axit sunfuric đặc vừa đóng vai trò chất xúc tác, vừa có tác dụng hút nước chuyển dịch cân bằng.' },
              { key: 'c', text: 'Sau khi đun cách thủy, thêm dung dịch NaCl bão hòa để este tách lớp nổi lên trên bề mặt.' },
              { key: 'd', text: 'Để tăng hiệu suất cần đun sôi mạnh hỗn hợp trên ngọn lửa đèn cồn trực tiếp không làm lạnh.' }
            ]
          }
        ];

        const q = chemPart2[(currentQuestionIdx - exerciseInfo.part1Count) % chemPart2.length];
        return {
          part: 'Phần II: Trắc nghiệm Đúng/Sai',
          number: qNum,
          type: 'true_false',
          statement: q.statement,
          items: q.items
        };
      }

      // Chemistry / AI Part III: Trả lời ngắn
      const chemPart3 = [
        { text: 'Cho 0,1 mol một este đơn chức X tác dụng vừa đủ với dung dịch NaOH thu được 6,8 gam muối natri fomat (HCOONa) và 4,6 gam một ancol Y. Khối lượng mol phân tử (M) của este X bằng bao nhiêu gam/mol?' },
        { text: 'Đốt cháy hoàn toàn 6,0 gam một este no, đơn chức, mạch hở X thu được 0,2 mol CO2. Số nguyên tử hiđro (H) trong một phân tử este X là bao nhiêu?' },
        { text: 'Xà phòng hóa hoàn toàn 17,8 gam tristearin (C17H35COO)3C3H5 bằng lượng vừa đủ dung dịch NaOH. Khối lượng (gam) glixerol thu được là bao nhiêu?' },
        { text: 'Cho 4,4 gam etyl axetat phản ứng hoàn toàn với 100 ml dung dịch NaOH 1M, đun nóng. Sau phản ứng, cô cạn dung dịch thu được bao nhiêu gam chất rắn khan?' },
        { text: 'Thủy phân hoàn toàn 8,9 gam chất béo triolein (C17H33COO)3C3H5 trong dung dịch KOH vừa đủ. Khối lượng (gam) KOH cần dùng là bao nhiêu?' },
        { text: 'Cho m gam etyl axetat tác dụng hoàn toàn với dung dịch NaOH vừa đủ thu được 8,2 gam muối natri axetat. Giá trị của m bằng bao nhiêu gam?' },
        { text: 'Đốt cháy hoàn toàn một este đơn chức X cần 0,35 mol O2, thu được 0,3 mol CO2 và 0,3 mol H2O. Số nguyên tử cacbon (C) trong phân tử X là bao nhiêu?' },
        { text: 'Thủy phân hoàn toàn 7,4 gam metyl axetat (CH3COOCH3) bằng 200 ml dung dịch KOH 1M. Cô cạn dung dịch sau phản ứng thu được bao nhiêu gam chất rắn khan?' },
        { text: 'Đun 12,0 gam axit axetic với 13,8 gam ancol etylic (xúc tác H2SO4 đặc) thu được 11,0 gam etyl axetat. Hiệu suất (%) của phản ứng este hóa là bao nhiêu %?' },
        { text: 'Hiđro hóa hoàn toàn 4,42 gam triolein (C17H33COO)3C3H5 cần vừa đủ bao nhiêu lít khí H2 ở điều kiện tiêu chuẩn (làm tròn 2 chữ số thập phân)?' }
      ];

      const q = chemPart3[(currentQuestionIdx - (exerciseInfo.part1Count + exerciseInfo.part2Count)) % chemPart3.length];
      return {
        part: 'Phần III: Trắc nghiệm Trả lời ngắn',
        number: qNum,
        type: 'short_answer',
        statement: q.text
      };
    }

    // MATH 12 DATASET (Đề thi Toán)
    const diagrams = {
      variationTable: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="480" height="150" viewBox="0 0 480 150">
            <rect x="10" y="10" width="460" height="130" rx="8" fill="#FAFAFD" stroke="#CBD5E1" strokeWidth="1.5" />
            <line x1="10" y1="48" x2="470" y2="48" stroke="#CBD5E1" strokeWidth="1.5" />
            <line x1="10" y1="84" x2="470" y2="84" stroke="#CBD5E1" strokeWidth="1.5" />
            <line x1="65" y1="10" x2="65" y2="140" stroke="#CBD5E1" strokeWidth="1.5" />
            
            <text x="35" y="34" fontSize="14" fontStyle="italic" fontWeight="700" fill="#4D308D" textAnchor="middle">x</text>
            <text x="35" y="70" fontSize="14" fontStyle="italic" fontWeight="700" fill="#4D308D" textAnchor="middle">y'</text>
            <text x="35" y="118" fontSize="14" fontStyle="italic" fontWeight="700" fill="#4D308D" textAnchor="middle">y</text>
            
            <text x="95" y="34" fontSize="13" fill="#334155" textAnchor="middle">-∞</text>
            <text x="195" y="34" fontSize="13" fontWeight="700" fill="#1E293B" textAnchor="middle">-1</text>
            <text x="315" y="34" fontSize="13" fontWeight="700" fill="#1E293B" textAnchor="middle">2</text>
            <text x="430" y="34" fontSize="13" fill="#334155" textAnchor="middle">+∞</text>
            
            <text x="145" y="70" fontSize="16" fontWeight="700" fill="#10B981" textAnchor="middle">+</text>
            <text x="195" y="70" fontSize="14" fill="#64748B" textAnchor="middle">0</text>
            <text x="255" y="70" fontSize="16" fontWeight="700" fill="#EF4444" textAnchor="middle">-</text>
            <text x="315" y="70" fontSize="14" fill="#64748B" textAnchor="middle">0</text>
            <text x="375" y="70" fontSize="16" fontWeight="700" fill="#10B981" textAnchor="middle">+</text>
            
            <text x="95" y="132" fontSize="12" fill="#64748B" textAnchor="middle">-∞</text>
            <text x="195" y="100" fontSize="13" fontWeight="700" fill="#4D308D" textAnchor="middle">5</text>
            <text x="315" y="134" fontSize="13" fontWeight="700" fill="#4D308D" textAnchor="middle">-4</text>
            <text x="430" y="100" fontSize="12" fill="#64748B" textAnchor="middle">+∞</text>
            
            <defs>
              <marker id="arrowY" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#6549A6" />
              </marker>
            </defs>
            <line x1="110" y1="128" x2="182" y2="105" stroke="#6549A6" strokeWidth="1.8" markerEnd="url(#arrowY)" />
            <line x1="208" y1="105" x2="302" y2="128" stroke="#6549A6" strokeWidth="1.8" markerEnd="url(#arrowY)" />
            <line x1="328" y1="128" x2="415" y2="105" stroke="#6549A6" strokeWidth="1.8" markerEnd="url(#arrowY)" />
          </svg>
          <p className="diagram-caption">Hình 1: Bảng biến thiên của hàm số y = f(x)</p>
        </div>
      ),
      pyramid3D: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="340" height="200" viewBox="0 0 340 200">
            <polygon points="170,25 60,150 210,165 280,120" fill="#F8FAFC" stroke="#1E293B" strokeWidth="1.5" />
            <line x1="60" y1="150" x2="130" y2="105" stroke="#94A3B8" strokeWidth="1.2" strokeDasharray="4,4" />
            <line x1="130" y1="105" x2="280" y2="120" stroke="#94A3B8" strokeWidth="1.2" strokeDasharray="4,4" />
            <line x1="170" y1="25" x2="130" y2="105" stroke="#94A3B8" strokeWidth="1.2" strokeDasharray="4,4" />
            <line x1="170" y1="25" x2="170" y2="135" stroke="#EF4444" strokeWidth="1.5" strokeDasharray="3,3" />
            <text x="175" y="85" fontSize="12" fontWeight="700" fill="#EF4444">h = 2a</text>
            <text x="168" y="18" fontSize="13" fontWeight="700" fill="#1E1B4B">S</text>
            <text x="45" y="155" fontSize="13" fontWeight="700" fill="#1E1B4B">A</text>
            <text x="212" y="180" fontSize="13" fontWeight="700" fill="#1E1B4B">B</text>
            <text x="288" y="125" fontSize="13" fontWeight="700" fill="#1E1B4B">C</text>
            <text x="120" y="100" fontSize="13" fontWeight="700" fill="#1E1B4B">D</text>
          </svg>
          <p className="diagram-caption">Hình 2: Khối chóp S.ABCD có diện tích đáy B = 6a² và chiều cao h = 2a</p>
        </div>
      ),
      waterTank3D: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="320" height="180" viewBox="0 0 320 180">
            <polygon points="60,75 180,75 180,150 60,150" fill="#EFF6FF" stroke="#2563EB" strokeWidth="1.5" />
            <polygon points="180,75 250,35 250,110 180,150" fill="#DBEAFE" stroke="#2563EB" strokeWidth="1.5" />
            <polygon points="60,75 130,35 250,35 180,75" fill="#BFDBFE" stroke="#2563EB" strokeWidth="1.5" />
            <text x="115" y="165" fontSize="13" fontWeight="700" fontStyle="italic" fill="#1E293B" textAnchor="middle">x</text>
            <text x="225" y="138" fontSize="13" fontWeight="700" fontStyle="italic" fill="#1E293B" textAnchor="middle">x</text>
            <text x="45" y="115" fontSize="13" fontWeight="700" fontStyle="italic" fill="#2563EB" textAnchor="middle">h</text>
            <text x="150" y="110" fontSize="12" fontWeight="700" fill="#1E40AF" textAnchor="middle">V = 32 m³</text>
          </svg>
          <p className="diagram-caption">Hình 3: Mô hình bể nước đáy hình vuông cạnh x và chiều cao h</p>
        </div>
      ),
      cubicGraph: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="380" height="190" viewBox="0 0 380 190">
            <line x1="30" y1="100" x2="350" y2="100" stroke="#1E293B" strokeWidth="1.5" markerEnd="url(#arrow)" />
            <line x1="190" y1="175" x2="190" y2="20" stroke="#1E293B" strokeWidth="1.5" markerEnd="url(#arrow)" />
            <text x="355" y="104" fontSize="12" fontStyle="italic">x</text>
            <text x="185" y="15" fontSize="12" fontStyle="italic">y</text>
            <text x="178" y="114" fontSize="11">O</text>
            <path d="M 70,170 C 130,-10 160,20 190,100 C 220,180 250,210 310,30" fill="none" stroke="#6549A6" strokeWidth="2.2" />
            <circle cx="135" cy="45" r="3.5" fill="#EF4444" />
            <text x="110" y="40" fontSize="11" fill="#EF4444">(-1; 2)</text>
            <circle cx="245" cy="155" r="3.5" fill="#EF4444" />
            <text x="250" y="165" fontSize="11" fill="#EF4444">(1; -2)</text>
          </svg>
          <p className="diagram-caption">Hình 4: Đồ thị hàm số bậc ba y = f(x)</p>
        </div>
      )
    };

    // PART I: Trắc nghiệm 4 lựa chọn (1 - 15)
    if (currentQuestionIdx < 15) {
      const p1Data = [
        {
          title: 'Cho hàm số y = f(x) có bảng biến thiên như hình vẽ. Hàm số đã cho đạt cực đại tại điểm nào dưới đây?',
          diagram: diagrams.variationTable,
          options: [
            { key: 'A', text: 'x = -1' },
            { key: 'B', text: 'x = 2' },
            { key: 'C', text: 'x = 5' },
            { key: 'D', text: 'x = -4' }
          ]
        },
        {
          title: 'Tiệm cận ngang của đồ thị hàm số y = (2x - 1) / (x + 3) là đường thẳng có phương trình:',
          options: [
            { key: 'A', text: 'y = 2' },
            { key: 'B', text: 'x = -3' },
            { key: 'C', text: 'y = -3' },
            { key: 'D', text: 'x = 2' }
          ]
        },
        {
          title: 'Cho đồ thị hàm số bậc ba y = f(x) như hình vẽ bên dưới. Điểm cực tiểu của đồ thị hàm số là:',
          diagram: diagrams.cubicGraph,
          options: [
            { key: 'A', text: '(1; -2)' },
            { key: 'B', text: '(-1; 2)' },
            { key: 'C', text: 'x = 1' },
            { key: 'D', text: 'y = -2' }
          ]
        },
        {
          title: 'Thể tích của khối chóp có diện tích đáy B = 6a² và chiều cao h = 2a bằng:',
          diagram: diagrams.pyramid3D,
          options: [
            { key: 'A', text: 'V = 4a³' },
            { key: 'B', text: 'V = 12a³' },
            { key: 'C', text: 'V = 6a³' },
            { key: 'D', text: 'V = 2a³' }
          ]
        },
        {
          title: 'Trong không gian Oxyz, cho mặt cầu (S): (x - 1)² + (y + 2)² + (z - 3)² = 16. Tọa độ tâm I và bán kính R của (S) là:',
          options: [
            { key: 'A', text: 'I(1; -2; 3), R = 4' },
            { key: 'B', text: 'I(-1; 2; -3), R = 4' },
            { key: 'C', text: 'I(1; -2; 3), R = 16' },
            { key: 'D', text: 'I(-1; 2; -3), R = 16' }
          ]
        }
      ];

      const q = p1Data[currentQuestionIdx % p1Data.length];
      return {
        part: 'Phần I: Trắc nghiệm 4 lựa chọn',
        number: qNum,
        type: 'single_choice',
        statement: q.title,
        diagram: q.diagram,
        options: q.options
      };
    }

    // PART II: Trắc nghiệm Đúng / Sai
    if (currentQuestionIdx >= 15 && currentQuestionIdx < 15 + exerciseInfo.part2Count) {
      return {
        part: 'Phần II: Trắc nghiệm Đúng/Sai',
        number: qNum,
        type: 'true_false',
        statement: `Cho hàm số y = f(x) = x³ - 3x² + 2 có bảng biến thiên và đồ thị như hình vẽ. Xét tính đúng hay sai của các mệnh đề sau:`,
        diagram: diagrams.cubicGraph,
        items: [
          { key: 'a', text: 'Hàm số đã cho đồng biến trên các khoảng (-∞; 0) và (2; +∞).' },
          { key: 'b', text: 'Giá trị cực đại của hàm số bằng 2, đạt được tại x = 0.' },
          { key: 'c', text: 'Điểm uốn của đồ thị hàm số có tọa độ là I(1; 0).' },
          { key: 'd', text: 'Phương trình f(x) = m có 3 nghiệm thực phân biệt khi và chỉ khi -2 < m < 2.' }
        ]
      };
    }

    // PART III: Trả lời ngắn
    const shortAnswerSamples = [
      {
        text: 'Một bể chứa nước hình hộp chữ nhật có đáy là hình vuông cạnh x (mét) và chiều cao h (mét). Biết thể tích bể là 32 m³. Tìm giá trị cạnh đáy x (mét) để diện tích toàn phần của bể chứa là nhỏ nhất.',
        diagram: diagrams.waterTank3D
      },
      {
        text: 'Tìm giá trị lớn nhất của hàm số f(x) = x³ - 3x + 2 trên đoạn [0; 2].',
        diagram: diagrams.cubicGraph
      },
      {
        text: 'Trong không gian Oxyz, cho khối chóp tứ giác S.ABCD có thể tích V = 48. Tính chiều cao h của khối chóp biết diện tích đáy B = 12.',
        diagram: diagrams.pyramid3D
      }
    ];

    const sItem = shortAnswerSamples[(currentQuestionIdx - (15 + exerciseInfo.part2Count)) % shortAnswerSamples.length];
    return {
      part: 'Phần III: Trắc nghiệm Trả lời ngắn',
      number: qNum,
      type: 'short_answer',
      statement: sItem.text,
      diagram: sItem.diagram
    };
  }, [currentQuestionIdx, isChemistry, exerciseInfo]);

  return (
    <div className="exercise-taking-container">
      {/* 1. Top Navbar */}
      <header className="exam-top-navbar">
        <div className="exam-nav-left">
          <Link to="/student" className="exam-brand-logo">
            Academic Clarity
          </Link>
          <div className="exam-nav-divider" />
          <span className="exam-title-text">{exerciseInfo.title}</span>
        </div>

        <div className="exam-nav-right">
          <div className="exam-timer-pill">
            <Clock size={16} className="timer-icon" />
            <span>{formatTimer(timeLeft)}</span>
          </div>
          <button type="button" className="exam-icon-btn" aria-label="Help" title="Hướng dẫn làm bài">
            <HelpCircle size={20} />
          </button>
          <button type="button" className="exam-icon-btn" aria-label="Settings" title="Cài đặt giao diện">
            <Settings size={20} />
          </button>
        </div>
      </header>

      {/* 2. Main Workspace Body */}
      <div className="exam-workspace-body">
        {/* Left Palette Sidebar */}
        <aside className="exam-palette-sidebar">
          <div>
            <h3 className="palette-header-title">MỤC LỤC CÂU HỎI</h3>

            {/* Filter Toggle Actions */}
            <div className="palette-filter-actions">
              <button 
                type="button" 
                className={`palette-action-btn ${filterMode === 'flagged' ? 'active' : ''}`}
                onClick={() => setFilterMode(prev => prev === 'flagged' ? 'all' : 'flagged')}
              >
                <Flag size={14} fill={filterMode === 'flagged' ? '#DC2626' : 'none'} />
                <span>
                  {filterMode === 'flagged' ? 'Tất cả câu hỏi' : `Đã gắn cờ (${Object.values(flaggedQuestions).filter(Boolean).length})`}
                </span>
              </button>
            </div>

            {/* Flagged Filter Status Banner */}
            {filterMode === 'flagged' && (
              <div className="palette-flagged-banner">
                <div className="flagged-banner-left">
                  <span className="flagged-banner-dot" />
                  <span>Đang lọc: {Object.values(flaggedQuestions).filter(Boolean).length} câu gắn cờ</span>
                </div>
                <button 
                  type="button" 
                  className="flagged-banner-clear" 
                  onClick={() => setFilterMode('all')}
                  title="Hiện tất cả câu hỏi"
                >
                  Xóa lọc
                </button>
              </div>
            )}

            {/* Empty state when filtering flagged but no questions are flagged */}
            {filterMode === 'flagged' && Object.values(flaggedQuestions).filter(Boolean).length === 0 ? (
              <div className="palette-empty-flagged">
                <div className="empty-flag-icon-wrap">
                  <Flag size={24} className="empty-flag-icon" />
                </div>
                <h4 className="empty-flag-title">Chưa có câu gắn cờ</h4>
                <p className="empty-flag-desc">
                  Nhấn nút <strong>"Đánh dấu để xem lại"</strong> ở đầu mỗi câu hỏi để lưu vào danh sách này.
                </p>
                <button 
                  type="button" 
                  className="btn-back-all-questions" 
                  onClick={() => setFilterMode('all')}
                >
                  Xem tất cả câu hỏi
                </button>
              </div>
            ) : (
              /* Question Groups */
              <div className="palette-sections-list">
                {/* Group 1: Trắc nghiệm 4 lựa chọn */}
                <div className="palette-section-group">
                  <span className="palette-section-label">Trắc nghiệm 4 lựa chọn</span>
                  <div className="palette-buttons-grid">
                    {Array.from({ length: exerciseInfo.part1Count }, (_, i) => {
                      const qNum = i + 1;
                      const isAns = isQuestionAnswered(i);
                      const isFlagged = Boolean(flaggedQuestions[i]);
                      const isActive = currentQuestionIdx === i;
                      const isDimmed = filterMode === 'flagged' && !isFlagged;
                      return (
                        <button
                          key={qNum}
                          type="button"
                          className={`palette-num-btn ${isActive ? 'active' : ''} ${isAns ? 'answered' : ''} ${isFlagged ? 'flagged' : ''} ${isDimmed ? 'dimmed' : ''}`}
                          onClick={() => setCurrentQuestionIdx(i)}
                          title={`Câu ${qNum}${isFlagged ? ' (Đã gắn cờ)' : ''}${isAns ? ' (Đã trả lời)' : ''}`}
                        >
                          {qNum}
                          {isAns && !isActive && <span className="answered-dot" />}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Group 2: Trắc nghiệm Đúng/Sai */}
                <div className="palette-section-group">
                  <span className="palette-section-label">Trắc nghiệm Đúng/Sai</span>
                  <div className="palette-buttons-grid">
                    {Array.from({ length: exerciseInfo.part2Count }, (_, i) => {
                      const qIdx = i + exerciseInfo.part1Count;
                      const qNum = qIdx + 1;
                      const isAns = isQuestionAnswered(qIdx);
                      const isFlagged = Boolean(flaggedQuestions[qIdx]);
                      const isActive = currentQuestionIdx === qIdx;
                      const isDimmed = filterMode === 'flagged' && !isFlagged;
                      return (
                        <button
                          key={qNum}
                          type="button"
                          className={`palette-num-btn ${isActive ? 'active' : ''} ${isAns ? 'answered' : ''} ${isFlagged ? 'flagged' : ''} ${isDimmed ? 'dimmed' : ''}`}
                          onClick={() => setCurrentQuestionIdx(qIdx)}
                          title={`Câu ${qNum}${isFlagged ? ' (Đã gắn cờ)' : ''}${isAns ? ' (Đã trả lời)' : ''}`}
                        >
                          {qNum}
                          {isAns && !isActive && <span className="answered-dot" />}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Group 3: Trả lời ngắn */}
                <div className="palette-section-group">
                  <span className="palette-section-label">Trả lời ngắn</span>
                  <div className="palette-buttons-grid">
                    {Array.from({ length: exerciseInfo.part3Count }, (_, i) => {
                      const qIdx = i + exerciseInfo.part1Count + exerciseInfo.part2Count;
                      const qNum = qIdx + 1;
                      const isAns = isQuestionAnswered(qIdx);
                      const isFlagged = Boolean(flaggedQuestions[qIdx]);
                      const isActive = currentQuestionIdx === qIdx;
                      const isDimmed = filterMode === 'flagged' && !isFlagged;
                      return (
                        <button
                          key={qNum}
                          type="button"
                          className={`palette-num-btn ${isActive ? 'active' : ''} ${isAns ? 'answered' : ''} ${isFlagged ? 'flagged' : ''} ${isDimmed ? 'dimmed' : ''}`}
                          onClick={() => setCurrentQuestionIdx(qIdx)}
                          title={`Câu ${qNum}${isFlagged ? ' (Đã gắn cờ)' : ''}${isAns ? ' (Đã trả lời)' : ''}`}
                        >
                          {qNum}
                          {isAns && !isActive && <span className="answered-dot" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Submit Button on Sidebar Bottom */}
          <button 
            type="button" 
            className={`btn-submit-exam-sidebar ${isExamSubmitted && exerciseInfo.isExam ? 'submitted-locked' : ''}`}
            onClick={isExamSubmitted ? () => setIsReadOnlyReview(false) : handleOpenSubmitModal}
          >
            {isExamSubmitted ? (
              exerciseInfo.isExam ? (
                <>
                  <Lock size={15} />
                  <span>Đã nộp (Đã khóa)</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={15} />
                  <span>Đã nộp bài tập</span>
                </>
              )
            ) : (
              <>
                <span>{exerciseInfo.isExam ? 'Nộp bài thi' : 'Nộp bài tập'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </aside>

        {/* Center Question Viewport */}
        <main className="exam-question-viewport">
          {/* Readonly Review Banner */}
          {isExamSubmitted && isReadOnlyReview && (
            <div className={`exam-readonly-banner ${!exerciseInfo.isExam ? 'banner-practice' : ''}`}>
              <div className="readonly-banner-text">
                {exerciseInfo.isExam ? <Lock size={15} className="lock-icon" /> : <Sparkles size={15} className="practice-icon" />}
                <span>
                  <strong>{exerciseInfo.isExam ? 'Chế độ xem lại bài thi:' : 'Chế độ xem lại bài tập:'}</strong> {exerciseInfo.isExam ? `Đã nộp thành công lúc ${submissionResult?.formattedTime || 'trước đó'}. Bài thi này không cho phép làm lại.` : `Đã nộp lúc ${submissionResult?.formattedTime || 'trước đó'}. Bạn có thể bấm "Làm lại bài tập" bất cứ lúc nào.`}
                </span>
              </div>
              <button 
                type="button" 
                className="btn-exit-review-badge"
                onClick={() => navigate('/student/exercises')}
              >
                <span>Về Kho bài tập</span>
                <ArrowRight size={14} />
              </button>
            </div>
          )}

          <div className="question-card-panel">
            {/* Question Top Header */}
            <div className="question-card-header">
              <div className="question-header-left">
                <span className="question-section-pill">{questionData.part}</span>
                <span className="question-number-badge">
                  Câu {questionData.number}
                </span>
              </div>
              <button 
                type="button" 
                disabled={isReadOnlyReview}
                className={`btn-flag-review ${flaggedQuestions[currentQuestionIdx] ? 'flagged' : ''} ${isReadOnlyReview ? 'readonly' : ''}`}
                onClick={() => toggleFlag(currentQuestionIdx)}
              >
                <Flag size={15} fill={flaggedQuestions[currentQuestionIdx] ? '#DC2626' : 'none'} />
                <span>
                  {flaggedQuestions[currentQuestionIdx] ? 'Đã gắn cờ xem lại' : 'Đánh dấu để xem lại'}
                </span>
              </button>
            </div>

            {/* Question Statement */}
            <p className="question-statement-text">
              {questionData.statement}
            </p>

            {/* Dynamic Diagram */}
            {questionData.diagram ? (
              questionData.diagram
            ) : null}

            {/* ============================================================ */}
            {/* TYPE 1: MULTIPLE CHOICE 4 OPTIONS */}
            {/* ============================================================ */}
            {questionData.type === 'single_choice' && (
              <div className="question-options-wrapper">
                <h4 className="question-prompt-label">Chọn 01 đáp án đúng:</h4>
                <div className="question-options-grid">
                  {questionData.options.map((opt) => {
                    const isSelected = answers[currentQuestionIdx] === opt.key;
                    return (
                      <div
                        key={opt.key}
                        className={`option-select-box ${isSelected ? 'selected' : ''} ${isReadOnlyReview ? 'readonly-option' : ''}`}
                        onClick={() => !isReadOnlyReview && handleSelectOption(currentQuestionIdx, opt.key)}
                      >
                        <div className="option-letter-badge">{opt.key}</div>
                        <span className="option-content-text">{opt.text}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* TYPE 2: TRUE / FALSE MULTIPLE ITEMS */}
            {/* ============================================================ */}
            {questionData.type === 'true_false' && (
              <div className="question-tf-wrapper">
                <div className="tf-header-bar">
                  <h4 className="question-prompt-label">Xét tính Đúng / Sai của từng mệnh đề dưới đây:</h4>
                  <span className="tf-guide-note">Chọn một phương án [Đúng] hoặc [Sai] cho mỗi ý</span>
                </div>

                <div className="tf-items-list">
                  {questionData.items.map((item) => {
                    const currentTFState = answers[currentQuestionIdx] && typeof answers[currentQuestionIdx] === 'object'
                      ? answers[currentQuestionIdx][item.key]
                      : undefined;

                    return (
                      <div key={item.key} className={`tf-item-row ${currentTFState !== undefined ? 'has-answer' : ''}`}>
                        <div className="tf-item-content">
                          <span className="tf-sub-key-badge">{item.key})</span>
                          <span className="tf-sub-text">{item.text}</span>
                        </div>

                        <div className="tf-toggle-actions">
                          <button
                            type="button"
                            disabled={isReadOnlyReview}
                            className={`tf-btn btn-true ${currentTFState === true ? 'active' : ''}`}
                            onClick={() => !isReadOnlyReview && handleSelectTrueFalse(currentQuestionIdx, item.key, true)}
                          >
                            <CheckCircle2 size={16} />
                            <span>Đúng</span>
                          </button>

                          <button
                            type="button"
                            disabled={isReadOnlyReview}
                            className={`tf-btn btn-false ${currentTFState === false ? 'active' : ''}`}
                            onClick={() => !isReadOnlyReview && handleSelectTrueFalse(currentQuestionIdx, item.key, false)}
                          >
                            <XCircle size={16} />
                            <span>Sai</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* TYPE 3: SHORT ANSWER INPUT */}
            {/* ============================================================ */}
            {questionData.type === 'short_answer' && (
              <div className="question-short-answer-wrapper">
                <div className="short-answer-header-row">
                  <h4 className="question-prompt-label">Điền câu trả lời ngắn của bạn:</h4>
                  <span className="short-answer-rule-badge">Tối đa 4 ký tự • Phân tách thập phân bằng dấu ","</span>
                </div>

                <div className="short-answer-layout">
                  {/* Left: Input Box, 4-cell slots & Instructions */}
                  <div className="short-answer-input-side">
                    <div className="short-answer-input-container">
                      <span className="short-answer-prefix">Kết quả =</span>
                      <input 
                        type="text" 
                        maxLength={4}
                        readOnly={isReadOnlyReview}
                        className="short-answer-input-field" 
                        placeholder="VD: 3,75 hoặc -2,5"
                        value={typeof answers[currentQuestionIdx] === 'string' ? answers[currentQuestionIdx] : ''}
                        onChange={(e) => handleShortAnswerChange(currentQuestionIdx, e.target.value)}
                      />
                      <span className="char-count-pill">
                        {String(answers[currentQuestionIdx] || '').length}/4
                      </span>
                      {answers[currentQuestionIdx] && !isReadOnlyReview && (
                        <button 
                          type="button" 
                          className="btn-clear-input"
                          onClick={() => handleShortAnswerChange(currentQuestionIdx, '')}
                          title="Xóa kết quả"
                        >
                          <Delete size={16} />
                        </button>
                      )}
                    </div>

                    {/* 4 Optical Grid Slot Indicators */}
                    <div className="short-answer-slots-preview">
                      <span className="slots-label">Khung hiển thị 4 ô ký tự:</span>
                      <div className="slots-cells-row">
                        {[0, 1, 2, 3].map((slotIdx) => {
                          const strVal = String(answers[currentQuestionIdx] || '');
                          const charAtSlot = strVal[slotIdx] || '';
                          const isFilled = Boolean(charAtSlot);
                          return (
                            <div 
                              key={slotIdx} 
                              className={`slot-cell-box ${isFilled ? 'filled' : ''} ${strVal.length === slotIdx && !isReadOnlyReview ? 'active-typing' : ''}`}
                            >
                              <span className="slot-index-hint">Ô {slotIdx + 1}</span>
                              <span className="slot-char-val">{charAtSlot || '·'}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="short-answer-note-box">
                      <Info size={16} className="note-icon" />
                      <div className="note-text">
                        <strong>Quy tắc ghi đáp án trả lời ngắn:</strong>
                        <p>• Câu trả lời chỉ chứa tối đa <strong>4 ký tự</strong> (kể cả dấu âm <code>-</code> và dấu phẩy <code>,</code>).</p>
                        <p>• Ký tự số thập phân được phân chia bằng dấu phẩy <strong><code>,</code></strong> (Ví dụ: <code>3,75</code>, <code>-2,5</code>, <code>120</code>, <code>-14</code>).</p>
                        <p>• Nếu gõ dấu chấm <code>.</code>, hệ thống sẽ tự động chuyển thành dấu phẩy <code>,</code>.</p>
                      </div>
                    </div>
                  </div>

                  {/* Right: Quick Virtual Numpad */}
                  <div className="virtual-numpad-card">
                    <div className="numpad-header">
                      <Hash size={14} />
                      <span>Bàn phím số nhanh</span>
                    </div>
                    <div className="numpad-grid">
                      {['7', '8', '9', '4', '5', '6', '1', '2', '3', '+', '0', '-'].map((k) => (
                        <button
                          key={k}
                          type="button"
                          disabled={isReadOnlyReview}
                          className={`numpad-key-btn ${k === '+' ? 'key-plus' : ''} ${k === '-' ? 'key-minus' : ''}`}
                          onClick={() => handleNumpadPress(k)}
                        >
                          {k}
                        </button>
                      ))}
                      <button
                        type="button"
                        disabled={isReadOnlyReview}
                        className="numpad-key-btn key-comma"
                        onClick={() => handleNumpadPress(',')}
                        title="Dấu phẩy phân tách thập phân"
                      >
                        ,
                      </button>
                      <button
                        type="button"
                        disabled={isReadOnlyReview}
                        className="numpad-key-btn key-backspace"
                        onClick={() => handleNumpadPress('BACKSPACE')}
                        title="Xóa ký tự cuối (Backspace)"
                      >
                        <Delete size={15} />
                        <span style={{ fontSize: '11.5px' }}>Xóa</span>
                      </button>
                      <button
                        type="button"
                        disabled={isReadOnlyReview}
                        className="numpad-key-btn key-clear"
                        onClick={() => handleNumpadPress('CLEAR')}
                        title="Xóa toàn bộ kết quả"
                      >
                        <RotateCcw size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* 3. Bottom Fixed Navbar */}
      <footer className="exam-bottom-navbar">
        <div className="exam-progress-group">
          <span className="progress-label-text">
            Tiến độ hoàn thành: <strong>{answeredCount}</strong>/{totalQuestions} ({progressPercent}%)
          </span>
          <div className="progress-track-bar">
            <div 
              className="progress-filled-bar" 
              style={{ width: `${progressPercent}%` }} 
            />
          </div>
        </div>

        <div className="exam-nav-buttons-row">
          <button 
            type="button" 
            className="btn-nav-prev"
            disabled={currentQuestionIdx === 0}
            onClick={handlePrev}
          >
            <ArrowLeft size={16} />
            <span>Câu trước</span>
          </button>
          <button 
            type="button" 
            className="btn-nav-next"
            disabled={currentQuestionIdx === totalQuestions - 1}
            onClick={handleNext}
          >
            <span>Câu tiếp theo</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </footer>

      {/* ============================================================ */}
      {/* 4. CONFIRMATION SUBMIT MODAL DIALOG */}
      {/* ============================================================ */}
      {isSubmitModalOpen && (
        <div className="exam-modal-backdrop" onClick={() => setIsSubmitModalOpen(false)}>
          <div className="exam-submit-modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Modal Top Header */}
            <div className="submit-modal-header">
              <div className="modal-header-info">
                <div className="modal-icon-badge">
                  <Send size={20} />
                </div>
                <div>
                  <h3 className="modal-heading-title">
                    {exerciseInfo.isExam ? 'Xác nhận nộp bài thi' : 'Xác nhận nộp bài tập'}
                  </h3>
                  <p className="modal-heading-sub">{exerciseInfo.title} ({exerciseInfo.totalQuestions} câu / {exerciseInfo.durationMinutes} phút)</p>
                </div>
              </div>
              <button 
                type="button" 
                className="btn-close-modal"
                onClick={() => setIsSubmitModalOpen(false)}
                title="Đóng"
              >
                <X size={18} />
              </button>
            </div>

            {/* Quick Analytics Grid */}
            <div className="modal-analytics-grid">
              <div className="modal-stat-box box-answered">
                <div className="stat-box-icon">
                  <CheckCircle2 size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{answeredCount}/{totalQuestions}</span>
                  <span className="stat-box-desc">Câu đã làm</span>
                </div>
              </div>

              <div className={`modal-stat-box ${unansweredCount > 0 ? 'box-unanswered' : 'box-clean'}`}>
                <div className="stat-box-icon">
                  <AlertCircle size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{unansweredCount}</span>
                  <span className="stat-box-desc">Câu chưa làm</span>
                </div>
              </div>

              <div className="modal-stat-box box-flagged">
                <div className="stat-box-icon">
                  <Flag size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{flaggedCount}</span>
                  <span className="stat-box-desc">Đang gắn cờ</span>
                </div>
              </div>

              <div className="modal-stat-box box-time">
                <div className="stat-box-icon">
                  <Clock size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{formatTimer(timeLeft)}</span>
                  <span className="stat-box-desc">Thời gian còn</span>
                </div>
              </div>
            </div>

            {/* Progress Breakdown across 3 Parts */}
            <div className="modal-parts-progress-card">
              <span className="parts-progress-title">Tiến độ chi tiết từng phần bài làm:</span>
              <div className="parts-progress-list">
                <div className="part-progress-item">
                  <div className="part-progress-info">
                    <span>Phần I: Trắc nghiệm 4 lựa chọn</span>
                    <strong>{part1Answered}/{exerciseInfo.part1Count} câu</strong>
                  </div>
                  <div className="part-bar-track">
                    <div className="part-bar-fill fill-purple" style={{ width: `${(part1Answered / exerciseInfo.part1Count) * 100}%` }} />
                  </div>
                </div>

                <div className="part-progress-item">
                  <div className="part-progress-info">
                    <span>Phần II: Trắc nghiệm Đúng / Sai</span>
                    <strong>{part2Answered}/{exerciseInfo.part2Count} câu</strong>
                  </div>
                  <div className="part-bar-track">
                    <div className="part-bar-fill fill-indigo" style={{ width: `${(part2Answered / exerciseInfo.part2Count) * 100}%` }} />
                  </div>
                </div>

                <div className="part-progress-item">
                  <div className="part-progress-info">
                    <span>Phần III: Trả lời ngắn</span>
                    <strong>{part3Answered}/{exerciseInfo.part3Count} câu</strong>
                  </div>
                  <div className="part-bar-track">
                    <div className="part-bar-fill fill-violet" style={{ width: `${(part3Answered / exerciseInfo.part3Count) * 100}%` }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Strict Exam vs Regular Practice Notice */}
            {exerciseInfo.isExam ? (
              <div className="modal-strict-policy-notice">
                <ShieldAlert size={22} className="policy-notice-icon" />
                <div className="policy-notice-body">
                  <strong>Quy chế bài thi chính thức:</strong>
                  <p>
                    Đây là <strong>Bài thi</strong> (khác với bài tập rèn luyện). Sau khi xác nhận nộp bài, hệ thống sẽ tự động khóa và <strong>KHÔNG CHO PHÉP LÀM LẠI</strong>.
                  </p>
                </div>
              </div>
            ) : (
              <div className="modal-practice-policy-notice">
                <Sparkles size={22} className="policy-notice-icon-practice" />
                <div className="policy-notice-body-practice">
                  <strong>Lưu ý bài tập rèn luyện:</strong>
                  <p>
                    Đây là <strong>Bài tập thông thường</strong>. Sau khi nộp bài, hệ thống sẽ chấm điểm chi tiết và bạn <strong>HOÀN TOÀN CÓ THỂ LÀM LẠI / LUYỆN TẬP LẠI</strong> nhiều lần để nâng cao kết quả.
                  </p>
                </div>
              </div>
            )}

            {/* Modal Bottom Actions */}
            <div className="modal-submit-actions">
              <button
                type="button"
                className="btn-modal-back-check"
                onClick={() => setIsSubmitModalOpen(false)}
              >
                <ArrowLeft size={16} />
                <span>Tiếp tục làm bài</span>
              </button>

              <button
                type="button"
                className="btn-modal-final-submit"
                onClick={handleConfirmSubmit}
              >
                <span>{exerciseInfo.isExam ? 'Xác nhận nộp bài thi' : 'Xác nhận nộp bài tập'}</span>
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* 5. SUBMITTED RESULT / EXAM LOCKED FULLSCREEN OVERLAY */}
      {/* ============================================================ */}
      {isExamSubmitted && !isReadOnlyReview && (
        <div className="exam-submitted-overlay-screen">
          <div className="submitted-result-modal-box">
            <div className={`submitted-success-sparkle-icon ${!exerciseInfo.isExam ? 'practice-icon-glow' : ''}`}>
              <CheckCircle2 size={48} />
            </div>

            {exerciseInfo.isExam ? (
              <div className="submitted-lock-badge">
                <Lock size={13} />
                <span>Bài thi đã hoàn thành • Không cho phép làm lại</span>
              </div>
            ) : (
              <div className="submitted-practice-badge">
                <Sparkles size={13} />
                <span>Bài tập đã nộp • Cho phép làm lại không giới hạn</span>
              </div>
            )}

            <h2 className="submitted-success-title">
              {exerciseInfo.isExam ? 'Nộp bài thi thành công!' : 'Nộp bài tập thành công!'}
            </h2>
            <p className="submitted-success-desc">
              {exerciseInfo.isExam 
                ? 'Bài làm của bạn đã được ghi nhận an toàn vào hệ thống khảo sát.' 
                : `Bạn đã hoàn thành bài tập "${exerciseInfo.title}". Hệ thống đã chấm điểm tự động.`}
            </p>

            {/* Summary Stat Tiles */}
            <div className="submitted-result-tiles-row">
              <div className="result-tile-card">
                <span className="tile-label">Số câu đã làm</span>
                <span className="tile-value">{submissionResult?.answeredCount || answeredCount}/{totalQuestions}</span>
                <span className="tile-sub">({Math.round(((submissionResult?.answeredCount || answeredCount) / totalQuestions) * 100)}% hoàn thành)</span>
              </div>

              <div className="result-tile-card highlight-card">
                <span className="tile-label">Điểm đạt được</span>
                <span className="tile-value score-text">{submissionResult?.score || ((answeredCount / totalQuestions) * 10).toFixed(2)}</span>
                <span className="tile-sub">Thang điểm 10.0</span>
              </div>

              <div className="result-tile-card">
                <span className="tile-label">Thời điểm nộp</span>
                <span className="tile-value time-text">{submissionResult?.formattedTime || 'Vừa xong'}</span>
                <span className="tile-sub">Đã lưu kết quả</span>
              </div>
            </div>

            <div className={`submitted-guidance-card ${!exerciseInfo.isExam ? 'practice-guidance' : ''}`}>
              <Info size={18} className="guidance-icon" />
              <span>
                {exerciseInfo.isExam 
                  ? 'Theo quy chế, bài thi không thể làm lại. Điểm chính thức và lời giải chi tiết sẽ được giáo viên công bố sau khi hết hạn làm bài.'
                  : 'Đây là bài tập rèn luyện. Bạn có thể xem lại bài làm hoặc bấm "Làm lại bài tập" để luyện tập thêm.'}
              </span>
            </div>

            {/* Action Buttons */}
            <div className="submitted-actions-flex">
              {!exerciseInfo.isExam && (
                <button
                  type="button"
                  className="btn-retake-exam-active"
                  onClick={handleRetakeExercise}
                >
                  <RotateCcw size={16} />
                  <span>Làm lại bài tập</span>
                </button>
              )}

              <button
                type="button"
                className="btn-view-answers-readonly"
                onClick={() => setIsReadOnlyReview(true)}
              >
                <Eye size={16} />
                <span>Xem lại bài làm</span>
              </button>

              <button
                type="button"
                className="btn-return-exercises-hub"
                onClick={() => navigate('/student/exercises')}
              >
                <span>Về Kho bài tập</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
