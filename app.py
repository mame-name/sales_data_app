import streamlit as st
import pandas as pd

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
            # 1. グラフ配置エリア（最上部に移動）
            st.markdown("<h3 style='margin-top: 0px;'>📈 グラフ配置エリア</h3>", unsafe_allow_html=True)
            st.caption("※ここに抽出データから計算された各種チャートが描画されます。")
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
