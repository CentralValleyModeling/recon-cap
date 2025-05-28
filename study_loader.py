from collections import namedtuple

import pandas as pd
import yaml
from utils import list_files, load_data_mult, load_data
from pathlib import Path

# Scenario management
Study = namedtuple("Scenario", ["dv_path", "sv_path", "alias", "assumptions", "climate", "color"])



with open("constants/dvars.yaml", "r") as file:
    var_dict_dv = yaml.safe_load(file)
with open("constants/svars.yaml", "r") as file:
    var_dict_sv = yaml.safe_load(file)
with open("study_ledger.yaml", "r") as file:
    study_ledger = yaml.safe_load(file)

studies = [

    Study(r"dss_files\CCA1_v3.7.0__Baseline_LU100_SLR0_20241219",
          r"dss_files\CCA_SV_Danube_Adj_v1.9.dss",
          "CCA1", "Baseline", "Current", 1),


# ---------------------------------2043 CC50--------------------------------------
    Study(r"dss_files\CCA26_v3.7.0_BE_2043_50CC_LU100_SLR15_20241223.dss",  # Use CCA26
          r"dss_files\DCR2023_SV_Danube_2043_cc50_v1.9.dss",
          "CCA26", "Deteriorating System", "2043_CC50", 1),

    Study(r"dss_files\CCA4_v3.7.0__2043_50CC_LU100_SLR15_20241220.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc50_v1.9.dss",
          "CCA4", "Maintain", "2043_CC50", 1),

    Study(r"dss_files\CCA6_v3.7.0_A_2043_50CC_LU100_SLR15_20241227.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc50_v1.9.dss",
          "CCA6", "DCP", "2043_CC50", 1),

    Study(r"dss_files\CCA8_v3.7.0_D_2043_50CC_LU100_SLR15_20241223.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc50_v1.9.dss",
          "CCA8", "FIRO", "2043_CC50", 1),  

    Study(r"dss_files\CCA10_v3.7.0_C_2043_50CC_LU100_SLR15_20241226.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc50_v1.9.dss",
          "CCA10", "SOD Storage", "2043_CC50", 1),

    Study(r"dss_files\CCA12_v3.7.0_ACD_2043_50CC_LU100_SLR15_20241226.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc50_v1.9.dss",
          "CCA12", "Combo", "2043_CC50", 1),


# ---------------------------------2043 CC95--------------------------------------
    Study(r"dss_files\CCA27_v3.7.0_BE_2043_95CC_LU100_SLR30_20241224.dss",  # Use CCA27
          r"dss_files\DCR2023_SV_Danube_2043_cc95_v1.9.dss",
          "CCA27", "Deteriorating System", "2043_CC95", 1),

    Study(r"dss_files\CCA5_v3.7.0__2043_95CC_LU100_SLR30_20241227.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc95_v1.9.dss",
          "CCA5", "Maintain", "2043_CC95", 1),

    Study(r"dss_files\CCA7_v3.7.0_A_2043_95CC_LU100_SLR30_20241222.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc95_v1.9.dss",
          "CCA7", "DCP", "2043_CC95", 1),

    Study(r"dss_files\CCA9_v3.7.0_D_2043_95CC_LU100_SLR30_20241223.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc95_v1.9.dss",
          "CCA9", "FIRO", "2043_CC95", 1),  

    Study(r"dss_files\CCA11_v3.7.0_C_2043_95CC_LU100_SLR30_20241226.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc95_v1.9.dss",
          "CCA11", "SOD Storage", "2043_CC95", 1),

    Study(r"dss_files\CCA13_v3.7.0_ACD_2043_95CC_LU100_SLR30_20241226.dss",
          r"dss_files\DCR2023_SV_Danube_2043_cc95_v1.9.dss",
          "CCA13", "Combo", "2043_CC95", 1),

# ---------------------------------2085 CC50--------------------------------------
    Study(r"dss_files\CCA16_v3.7.0_G_2085_50CC_LU50_SLR55_20241219.dss",
          r"dss_files\SV_CS3_CCA_2085_CC50_Hydrology05.24.2024_LU50",
          "CCA16", "Maintain", "2085_CC50", 1),

    Study(r"dss_files\CCA18_v3.7.0_AG_2085_50CC_LU50_SLR55_20241223.dss",
          r"dss_files\SV_CS3_CCA_2085_CC50_Hydrology05.24.2024_LU50",
          "CCA18", "DCP", "2085_CC50", 1),

    Study(r"dss_files\CCA20_v3.7.0_DG_2085_50CC_LU50_SLR55_20241224.dss",
          r"dss_files\SV_CS3_CCA_2085_CC50_Hydrology05.24.2024_LU50",
          "CCA20", "FIRO", "2085_CC50", 1),  

    Study(r"dss_files\CCA22_v3.7.0_CG_2085_50CC_LU50_SLR55_20241224.dss",
          r"dss_files\SV_CS3_CCA_2085_CC50_Hydrology05.24.2024_LU50",
          "CCA22", "SOD Storage", "2085_CC50", 1),

    Study(r"dss_files\CCA24_v3.7.0_ACDG_2085_50CC_LU50_SLR55_20241222.dss",
          r"dss_files\SV_CS3_CCA_2085_CC50_Hydrology05.24.2024_LU50",
          "CCA24", "Combo", "2085_CC50", 1),


# ---------------------------------2085 CC75--------------------------------------
    Study(r"dss_files\CCA17_v3.7.0_G_2085_75CC_LU50_SLR105_20241223.dss",
          r"dss_files\SV_CS3_CCA_2085_CC75_Hydrology06.07.2024_LU50.dss",
          "CCA17", "Maintain", "2085_CC75", 1),

    Study(r"dss_files\CCA19_v3.7.0_AG_2085_75CC_LU50_SLR105_20241223.dss",
          r"dss_files\SV_CS3_CCA_2085_CC75_Hydrology06.07.2024_LU50.dss",
          "CCA19", "DCP", "2085_CC75", 1),

    Study(r"dss_files\CCA21_v3.7.0_DG_2085_75CC_LU50_SLR105_20241224.dss",
          r"dss_files\SV_CS3_CCA_2085_CC75_Hydrology06.07.2024_LU50.dss",
          "CCA21", "FIRO", "2085_CC75", 1),  

    Study(r"dss_files\CCA23_v3.7.0_CG_2085_75CC_LU50_SLR105_20241225.dss",
          r"dss_files\SV_CS3_CCA_2085_CC75_Hydrology06.07.2024_LU50.dss",
          "CCA23", "SOD Storage", "2085_CC75", 1),

    Study(r"dss_files\CCA25_v3.7.0_ACDG_2085_75CC_LU50_SLR105_20241223.dss",
          r"dss_files\SV_CS3_CCA_2085_CC75_Hydrology06.07.2024_LU50.dss",
          "CCA25", "Combo", "2085_CC75", 1),
]

date_map = pd.read_csv("constants/date_map.csv", index_col=0, parse_dates=True)

#load_data(studies, var_dict_dv, date_map, "dv", "dv_data.csv")
#load_data(studies, var_dict_sv, date_map, "sv", "sv_data.csv")
