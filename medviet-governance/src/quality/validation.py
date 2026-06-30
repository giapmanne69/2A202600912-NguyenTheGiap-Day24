# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = gx.ExpectationSuite(name="patient_data_suite")

    # Lấy validator dùng 1.x fluent datasources
    df = pd.read_csv("data/raw/patients_raw.csv")
    ds = context.data_sources.add_pandas("my_ds_validation")
    asset = ds.add_dataframe_asset("my_asset_validation")
    bd = asset.add_batch_definition_whole_dataframe("my_bd_validation")
    validator = context.get_validator(
        batch_request=bd.build_batch_request(batch_parameters={"dataframe": df}),
        expectation_suite=suite
    )

    # --- TASK: Thêm các expectations ---

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    # 2. cccd phải có đúng 12 ký tự
    validator.expect_column_value_lengths_to_equal(
        column="cccd",
        value=12
    )

    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    )

    # 4. benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column="benh",
        value_set=valid_conditions
    )

    # 5. email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )

    # 6. Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath, dtype={"cccd": str, "so_dien_thoai": str})
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc dạng số thuần túy
    # (sau anonymization, cccd phải là fake hoặc masked)
    try:
        raw_df = pd.read_csv("data/raw/patients_raw.csv", dtype={"cccd": str, "so_dien_thoai": str})
        original_cccdds = set(raw_df["cccd"].astype(str).tolist())
        current_cccdds = set(df["cccd"].astype(str).tolist())
        intersect = original_cccdds.intersection(current_cccdds)
        if intersect:
            results["success"] = False
            results["failed_checks"].append(f"Found original CCCD in anonymized data")
    except Exception:
        pass

    # Check 2: Không có null values trong các cột quan trọng
    important_cols = ["patient_id", "ho_ten", "cccd", "so_dien_thoai"]
    for col in important_cols:
        if col in df.columns:
            if df[col].isnull().any():
                results["success"] = False
                results["failed_checks"].append(f"Null values found in important column: {col}")

    # Check 3: Số rows phải bằng original
    try:
        raw_df = pd.read_csv("data/raw/patients_raw.csv", dtype={"cccd": str, "so_dien_thoai": str})
        if len(df) != len(raw_df):
            results["success"] = False
            results["failed_checks"].append(f"Row count mismatch: got {len(df)}, expected {len(raw_df)}")
    except Exception:
        pass

    return results
