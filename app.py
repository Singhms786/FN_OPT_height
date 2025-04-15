
import streamlit as st
import pandas as pd
from pulp import LpProblem, LpVariable, LpMaximize, LpBinary, lpSum
import io

st.set_page_config(page_title="Furnace Plate Optimizer with Thickness Constraint", layout="centered")
st.title("🔥 Furnace Plate Optimizer with Thickness Constraint")

# Upload file
uploaded_file = st.file_uploader("Upload Excel File (must have 'Plate Weight' and 'Plate Thickness')", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [col.strip() for col in df.columns]

    if "Plate Weight" not in df.columns or "Plate Thickness" not in df.columns:
        st.error("❌ Excel must include 'Plate Weight' and 'Plate Thickness' columns.")
    else:
        st.success("✅ File uploaded successfully.")
        st.dataframe(df.head())

        furnace = st.selectbox("Select Furnace", ["Furnace 1 (100 MT, 350 mm height)", "Furnace 2 (200 MT, 700 mm height)"])
        capacity = 100 if "1" in furnace else 200
        max_thickness = 350 if capacity == 100 else 700
        st.write(f"🔧 Selected capacity: {capacity} MT | Max Thickness: {max_thickness} mm")

        if st.button("Optimize"):
            prob = LpProblem("Furnace_Optimization_With_Height", LpMaximize)
            x = LpVariable.dicts("Select", df.index, cat=LpBinary)

            # Objective
            prob += lpSum([x[i] * df.loc[i, "Plate Weight"] for i in df.index])

            # Constraints
            prob += lpSum([x[i] * df.loc[i, "Plate Weight"] for i in df.index]) <= capacity
            prob += lpSum([x[i] * df.loc[i, "Plate Thickness"] for i in df.index]) <= max_thickness

            prob.solve()

            selected = df[[x[i].varValue == 1 for i in df.index]].copy()
            selected.reset_index(drop=True, inplace=True)
            total_weight = selected["Plate Weight"].sum()
            total_thickness = selected["Plate Thickness"].sum()

            st.success(f"Selected {len(selected)} plates.")
            st.metric("Total Weight", f"{total_weight:.2f} MT")
            st.metric("Total Thickness", f"{total_thickness:.0f} mm")
            st.dataframe(selected)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                selected.to_excel(writer, index=False, sheet_name="Optimized Plates")
            output.seek(0)

            st.download_button(
                label="📥 Download Optimized Plate Selection",
                data=output,
                file_name=f"Optimized_Furnace_{capacity}MT_Plates.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
