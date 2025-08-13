import pandas as pd
import yaml

date_map = pd.read_csv("constants/date_map.csv", index_col=0, parse_dates=True)
df_dv_orig = pd.read_csv("data/dv_data.csv", index_col=0, parse_dates=True)
df_dv = pd.read_csv("data/dv_data.csv", index_col=0, parse_dates=True)
scen_aliases = df_dv.Scenario.unique()

with open("constants/dvars.yaml", "r") as file:
    var_dict = yaml.safe_load(file)

# DV Derived Timeseries

df_dv["SWP_TA_CO_SOD"] = (
    df_dv["SWP_TA_TOTAL"]
    - df_dv["SWP_TA_FEATH"]
    - df_dv["SWP_TA_NBAY"]
    + df_dv["SWP_CO_TOTAL"]
    - df_dv["SWP_CO_FEATH"]
    - df_dv["SWP_CO_NBAY"]
)

df_dv["SWP_CO_SOD"] = df_dv["SWP_CO_TOTAL"] - df_dv["SWP_CO_FEATH"]- df_dv["SWP_CO_NBAY"]
df_dv["SWP_IN_SOD"] = df_dv["SWP_IN_TOTAL"] - df_dv["SWP_IN_FEATH"]- df_dv["SWP_IN_NBAY"]

df_dv["EXPORTACTUALTDIF"] = df_dv["EXPORTACTUALTD"] + df_dv["EXPORTACTUALIF"]

var_dict["SWP_TA_CO_SOD"] = {
    "alias": "SWP Table A and Article 56 (South of Delta)",
    "bpart": "SWP_TA_CO_SOD",
    "pathname": None,
    "table_convert": "cfs_taf",
    "table_display": "wy",
    "type": "Delivery",
    "units": "cfs",
    
}

var_dict["SWP_CO_SOD"] = {
    "alias": "Article 56 (South of Delta)",
    "bpart": "SWP_CO_SOD",
    "pathname": None,
    "table_convert": "cfs_taf",
    "table_display": "wy",
    "type": "Delivery",
    "units": "cfs",
}

var_dict["SWP_IN_SOD"] = {
    "alias": "Article 21 (South of Delta)",
    "bpart": "SWP_IN_SOD",
    "pathname": None,
    "table_convert": "cfs_taf",
    "table_display": "wy",
    "type": "Delivery",
    "units": "cfs",
}


var_dict["EXPORTACTUALTDIF"] = {
    "alias": "Total Exports from the Delta",
    "bpart": "EXPORTACTUALTDIF",
    "pathname": None,
    "table_convert": "cfs_taf",
    "table_display": "wy",
    "type": "Export",
    "units": "cfs",
}

# Special logic for the DCR:
# The DCR reports calendar year average of 1921 - 2021, but the full range of data
# does not exist for CY 2021 This logic extends the dataset by three months by
# averaging the last nine months of data
# Consistent with how the DCR excel report tool does it
df_dv_extended = pd.DataFrame()
for s in df_dv["Scenario"].unique():
    start_date_1 = "2021-01-31 23:59:59"
    end_date_1 = "2021-09-30 23:59:59"
    new_date_range = pd.date_range(
        start="2021-10-31 23:59:59", end="2021-12-31 23:59:59", freq="ME"
    )

    scenario_df = pd.DataFrame()
    lastpartialyear = pd.DataFrame()
    date_range = pd.date_range(
        start="2021-01-31 23:59:59", end="2021-09-30 23:59:59", freq="ME"
    )

    scenario_df = df_dv.loc[df_dv["Scenario"] == s]
    scenario_df.index = pd.to_datetime(scenario_df.index)

    lastpartialyear = scenario_df.loc[
        (scenario_df.index >= start_date_1) & (scenario_df.index <= end_date_1)
    ]
    # This is the average of the last nine months:
    lastpartialyearavg = lastpartialyear.groupby(["Scenario"]).mean(numeric_only=True)

    extended_df = pd.concat(
        [lastpartialyearavg] * len(new_date_range), ignore_index=True
    )
    extended_df["Scenario"] = s
    extended_df.index = new_date_range
    scenario_df = pd.concat([scenario_df, extended_df])
    df_dv_extended = pd.concat([df_dv_extended, scenario_df])
df_dv_extended.update(date_map)

df_dv = pd.DataFrame(df_dv_extended)

# Now do SV file mappings

df_sv = pd.read_csv("data/sv_data.csv", index_col=0, parse_dates=True)
with open("constants/svars.yaml", "r") as file:
    svar_dict = yaml.safe_load(file)

# SV Derived Timeseries
sac_b_map = [
    "I_BCN010",
    "I_BTL006",
    "I_CLR011",
    "I_COW014",
    "I_CWD018",
    "I_SCW008",
    "I_SHSTA",
    "I_WKYTN",
]
orovi_map = [
    "I_ALMNR",
    "I_ANTLP",
    "I_BTVLY",
    "I_BUCKS",
    "I_DAVIS",
    "I_EBF001",
    "I_FRMAN",
    "I_GZL009",
    "I_LGRSV",
    "I_MFF019",
    "I_MFF087",
    "I_MTMDW",
    "I_NFF029",
    "I_OROVL",
    "I_RVPHB",
    "I_SFF008",
    "I_SFF011",
    "I_SLYCK",
    "I_WBF006",
    "I_WBF015",
    "I_WBF030",
]
smart_map = [
    "I_BOWMN",
    "I_DER001",
    "I_DER004",
    "I_ENGLB",
    "I_FRDYC",
    "I_FRNCH",
    "I_JKSMD",
    "I_LCBRF",
    "I_MFY013",
    "I_NBLDB",
    "I_NFY029",
    "I_OGN005",
    "I_SCOTF",
    "I_SFD003",
    "I_SFY007",
    "I_SFY048",
    "I_SLT009",
    "I_SPLDG",
]
fol_i_map = [
    "I_ALD002",
    "I_ALD004",
    "I_ALOHA",
    "I_BSH003",
    "I_CAPLS",
    "I_CYN009",
    "I_DCC010",
    "I_ECHOL",
    "I_FOLSM",
    "I_FRMDW",
    "I_GERLE",
    "I_HHOLE",
    "I_ICEHS",
    "I_LKVLY",
    "I_LNG012",
    "I_LOONL",
    "I_LRB004",
    "I_MFA001",
    "I_MFA023",
    "I_MFA025",
    "I_MFA036",
    "I_NFA016",
    "I_NFA022",
    "I_NFA054",
    "I_NLC003",
    "I_NMA003",
    "I_NNA013",
    "I_PLC007",
    "I_PLM001",
    "I_PYR001",
    "I_RCK001",
    "I_RUB002",
    "I_RUB047",
    "I_SFA030",
    "I_SFA040",
    "I_SFA066",
    "I_SFA076",
    "I_SFR006",
    "I_SILVR",
    "I_SLC003",
    "I_SLF009",
    "I_SLV006",
    "I_SLV015",
    "I_STMPY",
    "I_UNVLY",
    "I_WBR001",
]
n_melon_map = [
    "I_ANG017",
    "I_BEARD",
    "I_BVC007",
    "I_CFS001",
    "I_DONLL",
    "I_LYONS",
    "I_MFS013",
    "I_MFS022",
    "I_MFS047",
    "I_MIL003",
    "I_NFS005",
    "I_NFS009",
    "I_NFS033",
    "I_PCRST",
    "I_RLIEF",
    "I_SFS030",
    "I_SFS033",
    "I_SPICE",
    "I_STS072",
]
dpr_i_map = ["I_ELENR", "I_HTCHY", "I_LLOYD", "I_PEDRO"]
lk_mc_map = ["I_MCLRE"]
mille_map = ["I_MLRTN"]

df_sv["SAC_B"] = df_sv[sac_b_map].sum(axis=1)
df_sv["OROVI"] = df_sv[orovi_map].sum(axis=1)
df_sv["SMART"] = df_sv[smart_map].sum(axis=1)
df_sv["FOL_I"] = df_sv[fol_i_map].sum(axis=1)
df_sv["N_MEL"] = df_sv[n_melon_map].sum(axis=1)
df_sv["DPR_I"] = df_sv[dpr_i_map].sum(axis=1)
df_sv["LK_MC"] = df_sv[lk_mc_map].sum(axis=1)
df_sv["MILLE"] = df_sv[mille_map].sum(axis=1)

df_sv["SAC4"] = df_sv["SAC_B"] + df_sv["OROVI"] + df_sv["SMART"] + df_sv["FOL_I"]
df_sv["SJR4"] = df_sv["N_MEL"] + df_sv["DPR_I"] + df_sv["LK_MC"] + df_sv["MILLE"]

df_sv["8RI"] = df_sv["SAC4"] + df_sv["SJR4"]


# Add a variable that has only the final WYT for that WY
may_values = df_dv[df_dv['icm'] == 5].groupby(['Scenario','iwy'])['WYT_SAC_'].first()
df_dv["WYT_SAC_MAY"] = df_dv.set_index(['Scenario','iwy']).index.map(may_values)

df_sv["WYT_SAC_"] = df_dv_orig["WYT_SAC_"]  # add WYT back to the SV df

# CAP specific stuff
# There are only five unique WYT_SAC_ in the dv (one for each climate)
# filter out five of the unique ones from sv_df

unique_scenarios = ["CCA1", "CCA4", "CCA5", "CCA16", "CCA17"]
df_sv = df_sv[df_sv["Scenario"].isin(unique_scenarios)]
#print(df_sv)

# Name indexes
df_sv.index.name = "Date"
