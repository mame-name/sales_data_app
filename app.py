import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ページ設定（ワイドモードで左右分割を活かす）
st.set_page_config(layout="wide", page_title="営業データ分析システム")

# ==========================================
# 🎨 レイアウト微調整：左メニューをスリムに固定
# ==========================================
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    @media (min-width: 992px) {
        div[data-testid="stColumn"]:nth-of-type(1) {
            position: fixed;
            width: 22% !important; 
            max-height: 85vh;
            overflow-y: auto;
            padding-right: 15px;
        }
        div[data-testid="stColumn"]:nth-of-type(2) {
            margin-left: 25% !important; 
            width: 73% !important;        
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# ⚙️ データ処理関数
# ==========================================
@st.cache_data
def load_and_process_data(file):
    try:
        xl = pd.ExcelFile(file)
        target_sheet = 'Sheet1' if 'Sheet1' in xl.sheet_names else xl.sheet_names[0]
        df = pd.read_excel(file, sheet_name=target_sheet)
        df = df[~df.astype(str).apply(lambda x: x.str.contains('【')).any(axis=1)]
        df = df.dropna(how='all').reset_index(drop=True)
        df = df[::-1].reset_index(drop=True)
        if '売上日' in df.columns:
            df['売上日'] = pd.to_datetime(df['売上日'], errors='coerce')
            df = df.dropna(subset=['売上日'])
        return df
    except Exception as e:
        st.error(f"データ読込エラー: {e}")
        return None

# ==========================================
# 🧱 メインロジック
# ==========================================
left_col, right_col = st.columns([1, 3]) 

# 初期状態
processed_df = None
filtered_df = None
start_date = datetime(2026, 1, 1).date()
end_date = datetime(2026, 12, 31).date()

with left_col:
    st.subheader("📁 データ読込")
    uploaded_file = st.file_uploader("実績ファイルを選択", type=['xlsm', 'xlsx'], label_visibility="collapsed")
    
    st.markdown("---")
    st.subheader("⚙️ 条件選択")
    
    if uploaded_file:
        processed_df = load_and_process_data(uploaded_file)
        if processed_df is not None:
            start_date = processed_df['売上日'].min().date()
            end_date = processed_df['売上日'].max().date()
            
            # --- 日付入力（開始・終了） ---
            st.caption("📅 分析期間")
            with st.container(border=True):
                selected_start = st.date_input("開始", value=start_date)
                st.markdown("<div style='text-align: center; font-weight: bold;'>～</div>", unsafe_allow_html=True)
                selected_end = st.date_input("終了", value=end_date)
            
            # フィルター処理
            filtered_df = processed_df[
                (processed_df['売上日'].dt.date >= selected_start) & 
                (processed_df['売上日'].dt.date <= selected_end)
            ]
            
            # 営業担当選択
            unique_staff = ["全選択"] + sorted(processed_df['営業担当名'].dropna().unique().astype(str).tolist())
            selected_staff = st.selectbox("営業担当名", unique_staff)
            if selected_staff != "全選択":
                filtered_df = filtered_df[filtered_df['営業担当名'].astype(str) == selected_staff]
            
            # 請求先選択
            unique_clients = ["全選択"] + sorted(filtered_df['請求先名'].dropna().unique().astype(str).tolist())
            selected_client = st.selectbox("請求先名", unique_clients)
            if selected_client != "全選択":
                filtered_df = filtered_df[filtered_df['請求先名'].astype(str) == selected_client]

            st.markdown("---")
            st.metric(label="現在の該当件数", value=f"{len(filtered_df)} 件")
    else:
        st.info("👈 ファイルをアップロードしてください")

with right_col:
    if uploaded_file and processed_df is not None:
        # タイトル生成ロジック
        staff_txt = "全営業担当" if 'selected_staff' not in locals() or selected_staff == "全選択" else f"担当: {selected_staff}"
        if 'selected_client' not in locals() or selected_client == "全選択":
            main_title = f"📈 {staff_txt} 請求先別データ構成比"
            target_col, title_txt = '請求先名', "📊 請求先名毎の構成比（上位15社＋その他）"
        else:
            main_title = f"🔍 {staff_txt} 【{selected_client}】 品名別内訳"
            target_col, title_txt = '品名', "📊 品名毎の構成比（上位15品＋その他）"

        st.markdown(f"<h1 style='text-align: center; font-size: 26px;'>{main_title}</h1>", unsafe_allow_html=True)
        st.divider()

        if not filtered_df.empty:
            # グラフ生成
            df_pie = filtered_df[target_col].value_counts().reset_index()
            df_pie.columns = [target_col, '件数']
            # 上位15以外を「その他」へ
            if len(df_pie) > 15:
                df_top = df_pie.head(15).copy()
                df_top = pd.concat([df_top, pd.DataFrame({target_col: ['その他'], '件数': [df_pie.iloc[15:]['件数'].sum()]})])
                df_pie = df_top
            
            fig = px.pie(df_pie, names=target_col, values='件数', hole=0.4)
            fig.update_traces(domain=dict(x=[0.0, 0.55], y=[0.0, 1.0]))
            fig.update_layout(legend=dict(orientation="v", y=0.5, x=0.6))
            
            st.markdown(f"#### {title_txt}")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("## 📋 実績データ一覧")
            display_df = filtered_df.copy()
            display_df['売上日'] = display_df['売上日'].dt.strftime('%Y/%m/%d')
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("該当データがありません")
    else:
        st.info("👈 左側のパネルからデータを読み込んでください")
