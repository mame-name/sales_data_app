import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定（ワイドモードで左右分割を活かす）
st.set_page_config(layout="wide", page_title="営業データ分析システム")

# タイトルエリア
st.markdown("<h1 style='text-align: center;'>🤖 営業データ分析システム 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>実績データを読み込み、自動で整形・可視化を行います</p>", unsafe_allow_html=True) 
st.divider()

# ==========================================
# ⚙️ データ処理関数
# ==========================================
@st.cache_data
def load_and_process_data(file):
    """アップロードされたファイルをそのまま全列読み込み、【を含む行を除外する"""
    try:
        # Excelファイルの全シート名を取得して安全確認
        xl = pd.ExcelFile(file)
        sheet_names = xl.sheet_names
        
        # 'Sheet1' があればそれを使い、無ければ1番最初のシートを自動選択
        target_sheet = 'Sheet1' if 'Sheet1' in sheet_names else sheet_names[0]
        
        # 1. ファイルの最初の行をそのまま列名として全列読み込み
        df_raw = pd.read_excel(file, sheet_name=target_sheet)
        
        # 【クレンジング】データフレーム全体から「【」という文字が含まれる行を完全に除外
        df_raw = df_raw[~df_raw.astype(str).apply(lambda x: x.str.contains('【')).any(axis=1)]
        
        # すべて空の行を削除
        df_raw = df_raw.dropna(how='all').reset_index(drop=True)
        
        # 最新順（逆順）にしてインデックスを振り直す
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
left_col, right_col = st.columns([1, 2])

# グローバルでデータを保持する変数の初期化
processed_df = None

# ------------------------------------------
# 👈 左画面：データ入力 ＆ サマリー常時表示
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
    
    # ファイルがアップロードされている場合、左側にサマリー（メーター）を常時表示
    if uploaded_file:
        with st.spinner("🔄 実績データを読み込み中..."):
            processed_df = load_and_process_data(uploaded_file)
            
        if processed_df is not None:
            st.markdown("---")
            st.subheader("📊 データサマリー")
            
            # メーターの配置
            total_rows = len(processed_df)
            st.metric(label="解析データ総数", value=f"{total_rows} 件")
            st.metric(label="処理ステータス", value="正常 (【 行除外済)")


# ------------------------------------------
# 👉 右画面：メイン表示エリア（グラフ ＆ テーブル配置）
# ------------------------------------------
with right_col:
    if uploaded_file:
        if processed_df is not None:
            # 1. グラフ配置エリア（最上部）
            st.markdown("<h3 style='margin-top: 0px;'>📈 グラフ配置エリア</h3>", unsafe_allow_html=True)
            
            target_column = '請求先名' 
            
            if target_column in processed_df.columns:
                # 請求先名ごとの件数を集計
                df_pie = processed_df[target_column].value_counts().reset_index()
                df_pie.columns = [target_column, '件数']
                
                # データを件数の多い順に明示的に並び替え
                df_pie = df_pie.sort_values(by='件数', ascending=False).reset_index(drop=True)
                
                # Plotlyで円グラフを作成
                fig = px.pie(
                    df_pie, 
                    names=target_column, 
                    values='件数', 
                    title='請求先名毎のデータ構成比（12時スタート・大きい順）',
                    hole=0.3
                )
                
                # 【修正】rotation=0 にすることで、時計回りの時にぴったり12時（真上）スタートになります
                fig.update_traces(
                    sort=False, 
                    direction='clockwise', 
                    rotation=0
                )
                
                # グラフのレイアウト調整
                fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=400)
                
                # 画面に描画
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"⚠️ アップロードされたデータに『{target_column}』という列名が見つからないため、円グラフを描画できません。")
                st.caption(f"実際の列名一覧: {list(processed_df.columns)}")
            
            st.divider()
            
            # 2. データテーブル表示エリア（グラフの下）
            st.markdown("## 📋 実績データ一覧（全列表示）")
            if not processed_df.empty:
                st.dataframe(processed_df, use_container_width=True, height=450)
            else:
                st.warning("表示できるデータがありません。")
            
        else:
            st.warning("データの読み込みに失敗したため、表示できません。")
    else:
        # 初期状態の表示
        st.info("👈 まずは左側のパネルからファイル（Sheet1）をアップロードしてください。")
