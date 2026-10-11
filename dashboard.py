"""DataGuard: dynamic CSV/Excel data-quality dashboard with optional MySQL monitoring."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import inspect, text
from src.db_connection import get_engine

st.set_page_config(page_title="DataGuard | Monitor", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.1rem;max-width:1550px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#101d3a,#172b52 60%,#123b5c)}
[data-testid="stSidebar"] *{color:#eef5ff}
.hero{padding:1.4rem 1.6rem;border-radius:20px;background:linear-gradient(115deg,#101d3a,#2457d6 58%,#6c42d8);color:white;margin-bottom:1rem}
.hero h1{color:white;margin:0}.hero p{color:#e4ecff;margin:.35rem 0 0}
[data-testid="stMetric"]{padding:.85rem;border-radius:14px;border:1px solid #e4eaf4;box-shadow:0 5px 16px #1c2f5414}
</style>""", unsafe_allow_html=True)

SOURCE_TABLES=["customers","products","orders","order_items","payments","returns"]

@st.cache_resource
def get_cached_engine():
    try:
        engine=get_engine()
        with engine.connect() as conn: conn.execute(text("SELECT 1"))
        return engine, None
    except Exception as exc:
        return None, str(exc)

def read_mysql_tables(engine):
    names=set(inspect(engine).get_table_names())
    frames={}
    for name in SOURCE_TABLES:
        if name in names:
            frames[name]=pd.read_sql_query(text(f"SELECT * FROM `{name}`"),engine)
    return frames,names

def find_col(df, candidates):
    lookup={str(c).strip().lower():c for c in df.columns}
    return next((lookup[x] for x in candidates if x in lookup),None)

def check_file(df):
    rows=[]
    for col in df.columns:
        mask=df[col].isna() | df[col].astype("string").str.strip().eq("").fillna(False)
        for idx in df.index[mask]: rows.append({"Row":int(df.index.get_loc(idx))+2,"Column":str(col),"Issue":"Missing value","Details":f"{col} is blank"})
    dup=df.duplicated(keep=False)
    for pos, idx in enumerate(df.index[dup]): rows.append({"Row":int(df.index.get_loc(idx))+2,"Column":"All columns","Issue":"Duplicate row","Details":"This row matches another row"})
    for col in df.columns:
        low=str(col).strip().lower()
        if any(k in low for k in ["price","amount","cost","revenue","sales","total"]):
            values=pd.to_numeric(df[col],errors="coerce")
            bad=values.notna() & (values<0)
            for idx in df.index[bad]: rows.append({"Row":int(df.index.get_loc(idx))+2,"Column":str(col),"Issue":"Negative numeric value","Details":f"{col} is negative"})
            if "price" in low or "cost" in low:
                bad=values.notna() & (values<=0)
                for idx in df.index[bad]: rows.append({"Row":int(df.index.get_loc(idx))+2,"Column":str(col),"Issue":"Invalid price/cost","Details":f"{col} should be greater than zero"})
        if any(k in low for k in ["quantity","qty","stock"]):
            values=pd.to_numeric(df[col],errors="coerce")
            for idx in df.index[values.notna() & (values<0)]: rows.append({"Row":int(df.index.get_loc(idx))+2,"Column":str(col),"Issue":"Negative quantity/stock","Details":f"{col} cannot be negative"})
    return pd.DataFrame(rows,columns=["Row","Column","Issue","Details"])

def money(v):
    try:return f"₹{float(v):,.2f}"
    except (ValueError,TypeError):return f"{v:,}" if isinstance(v,(int,float)) else str(v)

def show_file_overview(df, filename):
    st.subheader(f"📄 Uploaded file overview — {filename}")
    num_cols=df.select_dtypes(include="number").columns.tolist()
    issues=check_file(df)
    missing=int(df.isna().sum().sum())
    duplicate=int(df.duplicated().sum())
    k=st.columns(5)
    k[0].metric("Total records",f"{len(df):,}")
    k[1].metric("Total columns",f"{len(df.columns):,}")
    k[2].metric("Missing values",f"{missing:,}")
    k[3].metric("Duplicate rows",f"{duplicate:,}")
    k[4].metric("Quality issues",f"{len(issues):,}")
    st.caption("These values are recalculated from the currently uploaded file. Upload another CSV/Excel file to update the dashboard.")
    left,right=st.columns([1.15,1])
    with left:
        st.markdown("#### Numeric column summary")
        if num_cols: st.dataframe(df[num_cols].describe().T.reset_index(names="Column"),use_container_width=True,hide_index=True)
        else: st.info("No numeric columns found in this file.")
    with right:
        st.markdown("#### Numeric data chart")
        if num_cols:
            chart_col=st.selectbox("Choose a numeric column",num_cols,key="file_chart_col")
            vals=pd.to_numeric(df[chart_col],errors="coerce").dropna()
            if len(vals): st.bar_chart(vals.reset_index(drop=True).rename("Value"))
            else: st.info("Selected column has no usable numeric values.")
        else: st.info("A chart appears when the file has numeric columns.")
    st.markdown("#### Data preview")
    st.dataframe(df.head(1000),use_container_width=True,hide_index=True)
    st.download_button("⬇ Download uploaded data",df.to_csv(index=False).encode("utf-8-sig"),"uploaded_data.csv","text/csv")
    st.markdown("#### Data quality findings")
    if issues.empty: st.success("No issues were detected by the current automatic checks.")
    else:
        st.dataframe(issues,use_container_width=True,hide_index=True)
        st.download_button("⬇ Download quality report",issues.to_csv(index=False).encode("utf-8-sig"),"uploaded_file_issues.csv","text/csv")

# Sidebar / global upload
st.sidebar.markdown("<div style='text-align:center;padding:8px 0 12px'><div style='font-size:40px'>🛡️</div><div style='font-size:25px;font-weight:850'>DataGuard</div><div style='font-size:11px;letter-spacing:1.4px;color:#a9c7ff'>DATA INTELLIGENCE</div></div>",unsafe_allow_html=True)
st.sidebar.caption("Quality & Business Monitoring")
upload=st.sidebar.file_uploader("Upload any CSV or Excel file",type=["csv","xlsx","xls"],key="global_upload")
upload_df=None
upload_error=None
if upload is not None:
    try:
        upload_df=pd.read_csv(upload) if upload.name.lower().endswith(".csv") else pd.read_excel(upload)
        if upload_df.empty: upload_error="The uploaded file has no data rows."
    except Exception as exc: upload_error=f"Could not read file: {exc}"
page=st.sidebar.radio("WORKSPACE",["🏠 Overview","🧪 Data Quality","📈 Anomaly Monitoring","🗄️ Data Explorer","📤 Upload File Check"])
page=page.split(" ",1)[1]
st.sidebar.divider()
st.sidebar.caption("CSV/Excel upload works without MySQL. MySQL pages use your local .env settings.")
st.markdown('<div class="hero"><h1>🛡️ DataGuard Monitoring Center</h1><p>Dynamic file analysis · Data quality intelligence · Optional MySQL business monitoring</p></div>',unsafe_allow_html=True)

engine,db_error=get_cached_engine()
mysql_frames={}; available=set(); db_name="not connected"
if engine is not None:
    try:
        mysql_frames,available=read_mysql_tables(engine)
        with engine.connect() as conn: db_name=conn.execute(text("SELECT DATABASE()")).scalar() or "default"
    except Exception as exc: db_error=str(exc); engine=None

if upload_error: st.error(upload_error)
if upload_df is not None: st.sidebar.success(f"Loaded {len(upload_df):,} rows · {len(upload_df.columns):,} columns")

if page=="Overview":
    if upload_df is not None and not upload_error:
        show_file_overview(upload_df,upload.name)
    elif mysql_frames:
        st.caption(f"MySQL database: `{db_name}` · Refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
        customers=mysql_frames.get("customers",pd.DataFrame()); products=mysql_frames.get("products",pd.DataFrame()); orders=mysql_frames.get("orders",pd.DataFrame()); returns=mysql_frames.get("returns",pd.DataFrame()); payments=mysql_frames.get("payments",pd.DataFrame())
        total_sales=pd.to_numeric(orders.get("total_amount",pd.Series(dtype=float)),errors="coerce").fillna(0).sum()
        issues=sum(len(check_file(d)) for d in mysql_frames.values())
        k=st.columns(5); k[0].metric("Customers",f"{len(customers):,}"); k[1].metric("Products",f"{len(products):,}"); k[2].metric("Orders",f"{len(orders):,}"); k[3].metric("Order value",money(total_sales)); k[4].metric("Returns",f"{len(returns):,}")
        st.markdown("#### Available MySQL tables")
        st.dataframe(pd.DataFrame([{"Table":n,"Rows":len(d),"Columns":len(d.columns)} for n,d in mysql_frames.items()]),use_container_width=True,hide_index=True)
        if not orders.empty and {"order_date","total_amount"}.issubset(orders.columns):
            sales=orders.copy(); sales["order_date"]=pd.to_datetime(sales["order_date"],errors="coerce"); sales["total_amount"]=pd.to_numeric(sales["total_amount"],errors="coerce"); sales=sales.dropna(subset=["order_date","total_amount"])
            if not sales.empty: st.markdown("#### Sales trend"); st.line_chart(sales.groupby(sales.order_date.dt.date)["total_amount"].sum())
    else:
        st.info("Upload a CSV or Excel file from the left sidebar to populate the dashboard. MySQL is optional for file analysis.")
        if db_error: st.caption("MySQL is currently unavailable; CSV/Excel analysis is still available.")
elif page=="Data Quality":
    if upload_df is not None and not upload_error:
        issues=check_file(upload_df)
        a,b,c=st.columns(3); a.metric("Issues",len(issues)); b.metric("Missing values",int(upload_df.isna().sum().sum())); c.metric("Duplicate rows",int(upload_df.duplicated().sum()))
        if issues.empty: st.success("No issues found.")
        else: st.dataframe(issues,use_container_width=True,hide_index=True); st.download_button("Download quality report",issues.to_csv(index=False).encode("utf-8-sig"),"quality_report.csv","text/csv")
    elif mysql_frames:
        st.caption("Upload a file for generic data checks, or explore the MySQL tables below.")
        for name,df in mysql_frames.items():
            with st.expander(f"{name} — {len(df):,} rows"):
                issues=check_file(df); st.metric("Detected generic issues",len(issues)); st.dataframe(issues.head(500),use_container_width=True,hide_index=True)
    else: st.info("Upload a CSV/Excel file in the sidebar. MySQL is not required.")
elif page=="Anomaly Monitoring":
    df=upload_df if upload_df is not None and not upload_error else mysql_frames.get("orders",pd.DataFrame())
    numeric=df.select_dtypes(include="number").columns.tolist() if not df.empty else []
    if not numeric: st.info("Upload a file or connect MySQL with numeric columns to run anomaly checks.")
    else:
        col=st.selectbox("Numeric metric",numeric); vals=pd.to_numeric(df[col],errors="coerce")
        threshold=st.slider("Outlier threshold (standard deviations)",1.0,4.0,2.0,0.5)
        mean=vals.mean(); std=vals.std(); out=df.loc[(vals-mean).abs()>threshold*std].copy() if pd.notna(std) and std>0 else df.iloc[0:0].copy()
        a,b,c=st.columns(3); a.metric("Rows checked",len(df)); b.metric("Average",f"{mean:,.2f}" if pd.notna(mean) else "N/A"); c.metric("Potential outliers",len(out))
        if out.empty: st.success("No values exceeded the selected threshold.")
        else: st.dataframe(out,use_container_width=True,hide_index=True); st.download_button("Download anomaly report",out.to_csv(index=False).encode("utf-8-sig"),"anomaly_report.csv","text/csv")
elif page=="Data Explorer":
    if upload_df is not None and not upload_error:
        st.subheader(f"Uploaded data: {upload.name}"); st.caption(f"{len(upload_df):,} rows · {len(upload_df.columns)} columns"); st.dataframe(upload_df,use_container_width=True,hide_index=True)
    elif mysql_frames:
        selected=st.selectbox("Choose MySQL table",list(mysql_frames)); df=mysql_frames[selected]; st.caption(f"{len(df):,} rows · {len(df.columns)} columns"); st.dataframe(df,use_container_width=True,hide_index=True); st.download_button("Download table CSV",df.to_csv(index=False).encode("utf-8-sig"),f"{selected}.csv","text/csv")
    else: st.info("Upload a CSV/Excel file in the sidebar. MySQL is optional.")
elif page=="Upload File Check":
    st.subheader("CSV/Excel File Checker")
    st.write("Upload any CSV or Excel workbook from the sidebar. Its row counts, column counts, missing values, duplicates, numeric summaries, charts and quality findings update automatically.")
    if upload_df is not None and not upload_error: show_file_overview(upload_df,upload.name)
    else:
        sample=pd.DataFrame({"product_name":["Keyboard","Mouse","Monitor","Laptop"],"quantity":[50,100,20,10],"price":[800,500,0,45000]})
        st.download_button("Download sample CSV",sample.to_csv(index=False).encode("utf-8-sig"),"stock_data_sample.csv","text/csv")
        st.info("Select a file using 'Upload any CSV or Excel file' in the left sidebar.")

if st.sidebar.button("↻ Refresh dashboard",use_container_width=True):
    st.cache_resource.clear(); st.rerun()
st.sidebar.caption("DataGuard · Dynamic file dashboard")
