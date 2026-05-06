import codecs

infoprex_data = [
    "CPR\tNOM\tLOCALIZACAO\tSAC\tPVP\tPCU\tDUC\tDTVAL\tCLA\tDUV\tV0\tV1\tV2\tV3\tV4\tV5\tV6\tV7\tV8\tV9\tV10\tV11\tV12\tV13\tV14",
    "1234567\tPROD1\tIlha\t10\t10.5\t8.0\t01/01/2026\t10/2026\tLAB1\t15/05/2026\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1\t1",
    "1234567\tPROD1\tColmeias\t5\t10.5\t8.0\t01/01/2026\t10/2026\tLAB1\t14/05/2026\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0",
    "1000000\tLOCALPROD\tIlha\t0\t5.0\t4.0\t\t\tLAB2\t15/05/2026\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0",
    "ABCDEFG\tINVALID_CODE\tIlha\t1\t1.0\t0.5\t\t\tLAB1\t15/05/2026\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0",
    "7654321\tPROD3\tIlha\t0\t20.0\t15.0\t\t\tLAB3\t15/05/2026\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2\t2",
]

with codecs.open("tests/fixtures/infoprex_mini.txt", "w", encoding="utf-16") as f:
    f.write("\ufeff")
    f.write("\n".join(infoprex_data) + "\n")

print("Rewritten infoprex_mini.txt")
