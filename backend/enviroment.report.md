A. ENVIROMENT TRONG PROJECT 

-Tập hợp các điều kiện, cấu hình và tài nguyên mà ứng dụng sử dụng để chạy
(môi trường để ứng dụng chạy) 

B. ENVIROMENT THÔNG THƯỜNG
 1.  Development (Dev)

-Môi trường dành cho lập trình viên.

 Đặc điểm:
   Chạy trên máy cá nhân.
   Có thể bật log và debug.
   Dùng dữ liệu thử nghiệm. 

 2. Testing / Staging

 Môi trường để kiểm thử trước khi đưa sản phẩm lên production.

 Đặc điểm:
   Gần giống Production.
   Dùng để QA hoặc tester kiểm tra.
   Phát hiện lỗi trước khi phát hành.

 3. Production (Prod)

 Môi trường mà người dùng cuối sử dụng.

 Đặc điểm:
   Tối ưu hiệu năng.
   Tắt debug.
   Kết nối cơ sở dữ liệu thật.
   Yêu cầu bảo mật cao.

C. ENVIROMENT VARIEABLES

-Là các biến cấu hình mà chương trình sử dụng. gồm

  +Cấu hình Server

  +Database

  +API

  +Authentication & Security

  +Email

  +Logging(dubug, info, warn,error)
  
*.env là chỉ là file để lưu trữ ENVIROMENT VARIEABLE