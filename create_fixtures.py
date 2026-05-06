import codecs
import os

import pandas as pd

os.makedirs("tests/fixtures", exist_ok=True)

# 1. infoprex_mini.txt (UTF-16 with BOM, tab separated)
infoprex_data = [
    "CÓDIGO\tDESCRIÇÃO\tLOCALIZACAO\tP.CUSTO\tPVP\tSTOCK\tDUC\tDTVAL\tM1\tM2\tM3\tM4\tM5\tM6\tM7\tM8\tM9\tM10\tM11\tM12\tM13\tM14\tM15\tTotais",
    "1234567\tPRODUTO A\tFARMACIA ILHA\t10.0\t15.0\t5\t2\t2026-12-01\t0\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\t13\t14\t110",
    "1234567\tPRODUTO A\tFARMACIA SOUTO\t10.0\t15.0\t2\t0\t\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t15",
    "7654321\tPRODUTO B\tFARMACIA ILHA\t5.0\t8.0\t0\t0\t\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0",
    "1999999\tLOCAL C\tFARMACIA ILHA\t2.0\t4.0\t10\t5\t2027-01-01\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t30",
]

with codecs.open("tests/fixtures/infoprex_mini.txt", "w", encoding="utf-16") as f:
    f.write("\ufeff")
    f.write("\n".join(infoprex_data) + "\n")

# 2. codigos_sample.txt
codigos_data = [
    "1234567",
    "7654321",
    "1111111",
    "2222222",
    "3333333",
    "invalid_code",
    "  ",
    "abc",
    "4444444",
]
with open("tests/fixtures/codigos_sample.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(codigos_data) + "\n")

# 3. marcas_sample.csv
marcas_data = [
    "COD;MARCA",
    "1234567;MARCA A",
    "7654321;MARCA B",
    "2222222;MARCA C",
    "invalid;",
    "3333333;None",
]
with open("tests/fixtures/marcas_sample.csv", "w", encoding="utf-8") as f:
    f.write("\n".join(marcas_data) + "\n")

# 4. shortages_sample.xlsx
df_shortages = pd.DataFrame(
    {
        "Número de registo": ["1234567", "7654321", "2222222"],
        "Data de início de rutura": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        "Data prevista para reposição": pd.to_datetime(["2027-01-01", "2027-02-01", "2027-03-01"]),
        "Nome do medicamento": ["A", "B", "C"],
        "Data da Consulta": ["2025-05-01", "2025-05-01", "2025-05-01"],
    }
)
df_shortages.to_excel("tests/fixtures/shortages_sample.xlsx", index=False)

# 5. donotbuy_sample.xlsx
df_donotbuy = pd.DataFrame(
    {
        "CNP": ["1234567", "7654321", "1234567"],
        "FARMACIA": ["FARMACIA ILHA", "FARMACIA SOUTO", "FARMACIA SOUTO"],
        "DATA": ["01-01-2026", "02-01-2026", "03-01-2026"],
    }
)
df_donotbuy.to_excel("tests/fixtures/donotbuy_sample.xlsx", index=False)

print("Fixtures created successfully.")
