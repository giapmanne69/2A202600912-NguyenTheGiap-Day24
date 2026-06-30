# src/pii/anonymizer.py
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        import random
        import hashlib
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", 
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", 
                                 {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", 
                           {"new_value": f"{random.randint(0,9)}" + "".join([str(random.randint(0,9)) for _ in range(11)])}),
                "VN_PHONE": OperatorConfig("replace", 
                            {"new_value": f"0{random.choice([3,5,7,8,9])}" + "".join([str(random.randint(0,9)) for _ in range(8)])}),
            }
        elif strategy == "mask":
            def mask_func(val):
                # If there are spaces, mask word by word keeping the first character
                val_str = str(val).strip()
                if " " in val_str:
                    words = val_str.split()
                    return " ".join([w[0] + "*" * (len(w) - 1) if len(w) > 1 else w for w in words])
                else:
                    return "*" * len(val_str)

            operators = {
                "PERSON": OperatorConfig("custom", {"custom_anonymizer": mask_func}),
                "EMAIL_ADDRESS": OperatorConfig("custom", {"custom_anonymizer": mask_func}),
                "VN_CCCD": OperatorConfig("custom", {"custom_anonymizer": mask_func}),
                "VN_PHONE": OperatorConfig("custom", {"custom_anonymizer": mask_func}),
            }
        elif strategy == "hash":
            def hash_func(val):
                return hashlib.sha256(str(val).encode()).hexdigest()

            operators = {
                "PERSON": OperatorConfig("custom", {"custom_anonymizer": hash_func}),
                "EMAIL_ADDRESS": OperatorConfig("custom", {"custom_anonymizer": hash_func}),
                "VN_CCCD": OperatorConfig("custom", {"custom_anonymizer": hash_func}),
                "VN_PHONE": OperatorConfig("custom", {"custom_anonymizer": hash_func}),
            }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        import random
        df_anon = df.copy()

        # Cột text (ho_ten, dia_chi, email)
        df_anon["ho_ten"] = df_anon["ho_ten"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))
        df_anon["dia_chi"] = df_anon["dia_chi"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))
        df_anon["email"] = df_anon["email"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))

        # Cột cccd, so_dien_thoai
        df_anon["cccd"] = [
            f"{random.randint(0,9)}" + "".join([str(random.randint(0,9)) for _ in range(11)])
            for _ in range(len(df_anon))
        ]
        df_anon["so_dien_thoai"] = [
            f"0{random.choice([3,5,7,8,9])}" + "".join([str(random.randint(0,9)) for _ in range(8)])
            for _ in range(len(df_anon))
        ]

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col]:
                val_str = str(value).strip()
                # Defensive check: if leading zeros were stripped, pad them back
                if col == "cccd" and val_str.isdigit() and len(val_str) < 12:
                    val_str = val_str.zfill(12)
                elif col == "so_dien_thoai" and val_str.isdigit() and len(val_str) < 10:
                    val_str = val_str.zfill(10)

                total += 1
                results = detect_pii(val_str, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
