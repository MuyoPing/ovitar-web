# OVITAR (Project Real Aesthetic Clone & License Key System)

공식 웹사이트 및 라이선스 키 관리자 시스템입니다.

## 🚀 주요 구성 파일
- index.html: 메인 랜딩 페이지 (Real 테마, 키 등록 모달, 공기역학적 벡터 로고)
- updates.html: 업데이트 내역 페이지
- 
otice.html: 공지사항 페이지
- dmin.html: 실시간 관리자 대시보드 (lunatop3)
- key_server.py: 로컬 SQLite 라이선스 키 및 인증 서버 (port 5500)
- keys.db: 유저 계정 및 라이선스 키 데이터베이스

## 🔑 실행 방법
1. 로컬 키 관리 서버 실행:
   `ash
   python key_server.py
   `
2. 웹사이트 접속:
   - 메인 웹사이트: http://127.0.0.1:5500/index.html
   - 관리자 대시보드: http://127.0.0.1:5500/admin.html (계정: lunatop3 / sd3411@11)
