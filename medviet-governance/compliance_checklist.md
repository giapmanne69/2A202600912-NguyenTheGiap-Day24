# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | Envelope encryption (AES-256-GCM via SimpleVault) | ✅ Done | Infra Team |
| Audit logging | FastAPI authorization logs + audit events to AWS CloudTrail | ✅ Done | Platform Team |
| Breach detection | Prometheus alerts on authentication anomalies & spikes | ✅ Done | Security Team |

## F. Solution Details for Technical Controls
- **Audit Logging**: Implement custom middleware in FastAPI to log access actions containing user ID, resource accessed, timestamp, and action result to a centralized logging server (e.g. AWS CloudWatch or EFK stack).
- **Breach Detection**: Integrate Prometheus metrics for endpoint access counters and setup Grafana dashboards with alerts triggered by abnormal patterns (e.g., rapid bursts of 403 Forbidden responses, unusual API loads, or raw data access anomalies).
