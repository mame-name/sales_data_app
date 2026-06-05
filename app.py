import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定（ワイドモードで左右分割を活かす）
st.set_page_config(layout="wide", page_title="営業データ分析システム")

# ==========================================
# 🎨 左右独立スクロール・固定表示のためのCSS注入
# ==========================================
st.markdown(
    """
    <style>
    /* Streamlit標準のコンテナの余白を調整 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 左側のカラムを画面に固定するスタイル */
    @media (min-width: 992px) {
        div[data-testid="stColumn"]:nth-of-type(1) {
            position: fixed;
            width: 28% !important; /* 左画面の幅を固定 */
            max-height: 85vh;
            overflow-y: auto;      /* 左側が長くなった場合も独自スクロール */
            padding-right: 10px;
        }
        
        div[data-testid="stColumn"]:nth-of-type(2) {
            margin-left: 35% !important; /* 右画面が左画面と被らないようにマージンをあける */
            width: 65% !important;
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
    """アップロードされたファイルをそのまま全列読み込み、【を含む行を除外する"""
    try:
        xl = pd.ExcelFile(file)
        sheet_names = xl.sheet_names
        target_sheet = 'Sheet1' if 'Sheet1' in sheet_names else sheet_names[0]
        
        df_raw = pd.read_excel(file, sheet_name=target_sheet)
        df_raw = df_raw[~df_raw.astype(str).apply(lambda x: x.str.contains('【')).any(axis=1)]
        df_raw = df_raw.dropna(how='all').reset_index(drop=True)
        
        return df_raw[::-1].reset_index(drop=True)
        
    except ModuleNotFoundError as e:
        st.error("🚨 必須ライブラリが不足しています。ターミナルで `pip install openpyxl` を実行してください。")
        return None
    except Exception as e:
        if "openpyxl" in str(e):
            st.error("🚨 Excelの読み込みにライブラリが必要です。ターミナルで `pip install openpyxl` を実行してください。")
        else:
            st.error(f"データ処理エラー: {e}")
        return None


# ==========================================
# 🧱 左右分割レイアウトの作成
# ==========================================
left_col, right_col = st.columns([1, 3])

# グローバルでデータを保持する変数の初期化
processed_df = None

# ------------------------------------------
# 👈 左画面：データ入力 ＆ サマリー（画面左側に常時固定表示）
# ------------------------------------------
with left_col:
    st.subheader("📁 データソース読込")
    uploaded_file = st.file_uploader("実績XLSMファイルを選択してください", type=['xlsm', 'xlsx'], label_visibility="collapsed")
    
    st.markdown("---")
    st.subheader("⚙️ 条件選択")
    st.caption("※ファイル読み込み後に選択可能になります（現在は外枠のみ）。")
    
    target_region = st.selectbox("対象エリア", ["全エリア", "関東", "関西", "その他"], disabled=True)
    target_category = st.selectbox("製品カテゴリー", ["すべて", "カテゴリーA", "カテゴリーB"], disabled=True)
    analysis_range = st.slider("分析期間 (ヶ月)", min_value=1, max_value=12, value=3, disabled=True)
    
    if uploaded_file:
        with st.spinner("🔄 実績データを読み込み中..."):
            processed_df = load_and_process_data(uploaded_file)
            
        if processed_df is not None:
            st.markdown("---")
            st.subheader("📊 データサマリー")
            total_rows = len(processed_df)
            st.metric(label="解析データ総数", value=f"{total_rows} 件")
            st.metric(label="処理ステータス", value="正常 (【 行除外済)")


# ------------------------------------------
# 👉 右画面：メイン表示エリア（グラフ ＆ テーブルを配置し、独立スクロール）
# ------------------------------------------

with right:
    st.markdown("<h1 style='text-align: center;'>🤖 営業データ分析システム 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>実績データを読み込み、自動で整形・可視化を行います</p>", unsafe_allow_html=True)
    st.divider()

with right_col:
    if uploaded_file:
        if processed_df is not None:
            # 1. グラフ配置エリア（最上部）
            st.markdown("<h3 style='margin-top: 0px;'>📈 グラフ配置エリア</h3>", unsafe_allow_html=True)
            
            target_column = '請求先名' 
            
            if target_column in processed_df.columns:
                original_unique_count = processed_df[target_column].nunique()
                
                df_pie = processed_df[target_column].value_counts().reset_index()
                df_pie.columns = [target_column, '件数']
                df_pie = df_pie.sort_values(by='件数', ascending=False).reset_index(drop=True)
                
                top_n = 15
                if len(df_pie) > top_n:
                    df_top = df_pie.head(top_n).copy()
                    other_count = df_pie.iloc[top_n:]['件数'].sum()
                    df_other = pd.DataFrame([{target_column: 'custom_other', '件数': other_count}])
                    df_pie = pd.concat([df_top, df_other], ignore_index=True)
                
                total_count = df_pie['件数'].sum()
                df_pie['割合'] = (df_pie['件数'] / total_count * 100).round(1)
                
                df_pie[target_column] = df_pie[target_column].replace('custom_other', 'その他')
                df_pie['凡例表示名'] = df_pie[target_column] + ' (' + df_pie['割合'].astype(str) + '%)'
                
                st.markdown(f"#### 📊 請求先名毎のデータ構成比（上位{top_n}社＋その他）")
                
                fig = px.pie(
                    df_pie, 
                    names='凡例表示名', 
                    values='件数', 
                    title='',
                    hole=0.4
                )
                
                # 【修正】
                # - textinfo='percent' に戻し、グラフ内は割合（％）のみを表示
                # - texttemplate で小数点第1位までの％表記（例：25.3%）に整形
                font_size = 14
                
                fig.update_traces(
                    sort=False, 
                    direction='clockwise', 
                    rotation=0,
                    textinfo='percent',
                    texttemplate='%{percent:.1%}', 
                    textposition='inside',
                    insidetextorientation='horizontal',
                    textfont=dict(size=font_size),       
                    insidetextfont=dict(size=font_size), 
                    hoverinfo='label+value+percent'
                )
                
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), 
                    height=500, 
                    showlegend=True,
                    annotations=[dict(text=f'総請求先数<br><b>{original_unique_count}社</b>', x=0.5, y=0.5, font_size=14, showarrow=False)]
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"⚠️ アップロードされたデータに『{target_column}』という列名が見つからないため、円グラフを描画できません。")
                st.caption(f"実際の列名一覧: {list(processed_df.columns)}")
            
            st.divider()
            
            # 2. データテーブル表示エリア（グラフの下）
            st.markdown("## 📋 実績データ一覧（全列表示）")
            if not processed_df.empty:
                st.dataframe(processed_df, use_container_width=True, height=500)
            else:
                st.warning("表示できるデータがありません。")
            
        else:
            st.warning("データの読み込みに失敗したため、表示できません。")
    else:
        st.info("👈 まずは左側のパネルからファイル（Sheet1）をアップロードしてください。")
