import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定（ワイドモードで左右分割を活かす）
st.set_page_config(layout="wide", page_title="営業データ分析システム")

# ==========================================
# 🎨 レイアウト微調整：左メニューをよりスリムに固定
# ==========================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    
    /* PC表示(横幅992px以上)の時、左画面を22%に絞り、右画面を75%に広げて有効活用 */
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
filtered_df = None

staff_options = ["全選択"]
client_options = ["全選択"]
selected_staff = "全選択"
selected_client = "全選択"
is_disabled = True

# ------------------------------------------
# 👈 左画面：スリム化したデータ入力＆条件選択
# ------------------------------------------
with left_col:
    st.subheader("📁 データ読込")
    uploaded_file = st.file_uploader("実績XLSMファイルを選択してください", type=['xlsm', 'xlsx'], label_visibility="collapsed")
    
    st.markdown("---")
    st.subheader("⚙️ 条件選択")
    
    if uploaded_file:
        with st.spinner("🔄 読込中..."):
            processed_df = load_and_process_data(uploaded_file)
            
        if processed_df is not None:
            is_disabled = False
            if '営業担当名' in processed_df.columns:
                unique_staff = processed_df['営業担当名'].dropna().unique().tolist()
                staff_options = ["全選択"] + sorted([str(s) for s in unique_staff])
    
    selected_staff = st.selectbox("営業担当名", staff_options, disabled=is_disabled)
    
    if processed_df is not None:
        filtered_df = processed_df.copy()
        if selected_staff != "全選択":
            filtered_df = filtered_df[filtered_df['営業担当名'].astype(str) == selected_staff]
        
        if '請求先名' in filtered_df.columns:
            unique_clients = filtered_df['請求先名'].dropna().unique().tolist()
            client_options = ["全選択"] + sorted([str(c) for c in unique_clients])
            
    selected_client = st.selectbox("請求先名", client_options, disabled=is_disabled)
    
    if filtered_df is not None and selected_client != "全選択":
        filtered_df = filtered_df[filtered_df['請求先名'].astype(str) == selected_client]

    if processed_df is not None and filtered_df is not None:
        st.markdown("---")
        st.subheader("📊 サマリー")
        total_rows = len(processed_df)
        match_rows = len(filtered_df)
        st.metric(label="データ総数", value=f"{total_rows} 件")
        st.metric(label="該当件数", value=f"{match_rows} 件")


# ------------------------------------------
# 👉 右画面：広くなったメイン表示（凡例右側 ＆ 円サイズ絶対固定）
# ------------------------------------------
with right_col:
    if not uploaded_file:
        main_title = "🤖 営業データ分析システム 🤖"
        sub_title = "実績データを読み込み、自動で整形・可視化を行います"
    else:
        staff_part = "全営業担当" if selected_staff == "全選択" else f"担当: {selected_staff}"
        if selected_client == "全選択":
            main_title = f"📈 {staff_part} 請求先別データ構成比"
            sub_title = "全体実績から上位15社の請求先シェアを分析しています"
            target_column = '請求先名'
            title_text = "📊 請求先名毎のデータ構成比（上位15社＋その他）"
            center_label = "総請求先数"
        else:
            main_title = f"🔍 {staff_part} 【{selected_client}】 品名別内訳"
            sub_title = f"選択された取引先（{selected_client}）が購入している製品群の構成比です"
            target_column = '品名'
            title_text = f"📊 品名毎のデータ構成比（上位15品＋その他）"
            center_label = "総品名数"

    st.markdown(f"<h1 style='text-align: center; font-size: 26px;'>{main_title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray; font-size: 14px;'>{sub_title}</p>", unsafe_allow_html=True) 
    st.divider()

    if uploaded_file:
        if processed_df is not None and filtered_df is not None:
            
            st.markdown("<h3 style='margin-top: 0px;'>📈 グラフ配置エリア</h3>", unsafe_allow_html=True)
            
            if target_column in filtered_df.columns:
                original_unique_count = filtered_df[target_column].nunique()
                
                df_pie = filtered_df[target_column].value_counts().reset_index()
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
                
                st.markdown(f"#### {title_text}")
                
                fig = px.pie(
                    df_pie, 
                    names='凡例表示名', 
                    values='件数', 
                    title='',
                    hole=0.4
                )
                
                font_size = 14
                
                # 【修正】
                # 円グラフの左右描画位置を「全体の左側（0.0〜0.55の間）」に厳密に固定。
                # これにより右側の凡例テキストがどんな長さになっても、円自体は常に同じサイズ・同じ位置を保ちます。
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
                    hoverinfo='label+value+percent',
                    domain=dict(x=[0.0, 0.55], y=[0.0, 1.0]) # ← 円のエリアを左半分に完全ロック！
                )
                
                # 【修正】凡例を右側(Vertical)へ戻しました。
                # 円グラフの中心も左側のエリアのセンター（x=0.275）へずらすことで、文字と真ん中の数字を完璧に一致させています。
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), 
                    height=500, 
                    showlegend=True,
                    legend=dict(
                        orientation="v",      # 縦並び（右側配置）
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=0.62                # 円グラフと被らない右側の適切な位置に配置
                    ),
                    annotations=[dict(
                        text=f'{center_label}<br><b>{original_unique_count}種類</b>', 
                        x=0.275,              # ← domainのx[0.0, 0.55]のちょうど真ん中
                        y=0.5, 
                        font_size=14, 
                        showarrow=False
                    )]
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"⚠️ 集計対象の列『{target_column}』がデータ内に見つからないためグラフを描画できません。")
            
            st.divider()
            
            # 2. データテーブル表示エリア
            st.markdown("## 📋 実績データ一覧（フィルター後）")
            if not filtered_df.empty:
                st.dataframe(filtered_df, use_container_width=True, height=500)
            else:
                st.warning("選択された条件に一致するデータがありません。")
            
        else:
            st.warning("データの読み込みに失敗したため、表示できません。")
    else:
        st.info("👈 まずは左側のパネルからファイル（Sheet1）をアップロードしてください。")
